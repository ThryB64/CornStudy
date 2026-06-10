"""V164 / T-REGIME-HMM — Détection non supervisée du régime de compression (Markov-switching).

Triangulation du START : si un modèle Markov-switching 2 états (sur Δbasis_z) date les bascules vers
le régime « compressing » au même moment que le label A (V153.start_events), alors le START est réel et
le label A bien posé ; sinon, le label A est en partie arbitraire.

Markov-switching = SECOND AVIS indépendant (aucune étiquette apprise). statsmodels optionnel.
DESCRIPTIF, ne touche pas la baseline. RESEARCH_ONLY_NOT_TRADING.
"""
from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR
from mais.research.v153_start_vs_inprogress import start_events

V164_DIR = ARTEFACTS_DIR / "v164"
V164_DIR.mkdir(parents=True, exist_ok=True)

MATCH_WINDOW = 5  # jours de tolérance pour qu'un start label-A « matche » une bascule HMM


def _fit_switching(dz: pd.Series) -> tuple[pd.Series, int] | None:
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
    mod = MarkovRegression(dz.to_numpy(), k_regimes=2, trend="c", switching_variance=True)
    try:
        res = mod.fit(em_iter=20, maxiter=100, disp=False)
    except Exception:  # noqa: BLE001
        return None
    smp = np.asarray(res.smoothed_marginal_probabilities)
    if smp.shape[0] != len(dz):  # statsmodels peut renvoyer (k, T)
        smp = smp.T
    dzv = dz.to_numpy()
    # moyenne de Δz pondérée par la proba lissée de chaque régime ; compressing = la plus négative
    wmeans = [float((smp[:, r] * dzv).sum() / max(smp[:, r].sum(), 1e-9)) for r in range(2)]
    compress_state = int(np.argmin(wmeans))
    prob = pd.Series(smp[:, compress_state], index=dz.index)
    return prob, compress_state


def run_v164(df: pd.DataFrame) -> dict[str, Any]:
    z = pd.to_numeric(df.get("ema_cbot_basis_zscore_52w"), errors="coerce")
    dz = z.diff().dropna()
    if len(dz) < 300:
        return {"version": "V164-HMM", "verdict": "TOO_FEW_OBS", "n": int(len(dz))}
    try:
        fit = _fit_switching(dz)
    except ImportError:
        return {"version": "V164-HMM", "verdict": "STATSMODELS_MISSING"}
    if fit is None:
        return {"version": "V164-HMM", "verdict": "FIT_FAILED"}
    prob, compress_state = fit

    # bascules : prob franchit 0.5 vers le haut (entrée en régime compressing)
    p = prob.to_numpy()
    entries_idx = [prob.index[i] for i in range(1, len(p)) if p[i] >= 0.5 and p[i - 1] < 0.5]

    # label A
    ev = start_events(df)
    start_idx = [df.index[i] for i in range(len(df)) if ev.iloc[i] == 1]

    # agrément : un start label-A est « confirmé » s'il existe une bascule HMM à <= MATCH_WINDOW jours
    entries_pos = np.array([df.index.get_loc(e) for e in entries_idx if e in df.index])
    offsets = []
    matched = 0
    for s in start_idx:
        sp = df.index.get_loc(s)
        if len(entries_pos):
            d = entries_pos - sp
            j = int(np.argmin(np.abs(d)))
            off = int(d[j])
            offsets.append(off)
            if abs(off) <= MATCH_WINDOW:
                matched += 1
    agreement = round(matched / len(start_idx), 3) if start_idx else None
    median_offset = int(np.median(np.abs(offsets))) if offsets else None

    # sens inverse : une bascule HMM correspond-elle à un départ label-A proche ? (HMM plus grossier)
    start_pos = np.array([df.index.get_loc(s) for s in start_idx])
    hmm_matched = 0
    for e in entries_pos:
        if len(start_pos) and np.min(np.abs(start_pos - e)) <= MATCH_WINDOW:
            hmm_matched += 1
    hmm_agreement = round(hmm_matched / len(entries_pos), 3) if len(entries_pos) else None

    triangulated = bool(hmm_agreement is not None and hmm_agreement >= 0.5)
    out = {
        "version": "V164-HMM",
        "verdict": "START_TRIANGULATED" if triangulated else "START_LABEL_ONLY_PARTIAL_AGREEMENT",
        "n_obs": int(len(dz)),
        "compress_state": int(compress_state),
        "n_hmm_regime_entries": len(entries_idx),
        "n_label_A_starts": len(start_idx),
        "agreement_rate_labelA_to_hmm": agreement,
        "agreement_rate_hmm_to_labelA": hmm_agreement,
        "median_abs_offset_days": median_offset,
        "match_window_days": MATCH_WINDOW,
        "frac_time_in_compressing_regime": round(float((p >= 0.5).mean()), 3),
        "interpretation": (
            f"HMM 2-états sur Δbasis_z : régime compressing = état {compress_state} "
            f"({round(float((p>=0.5).mean()),3)} du temps). Sens HMM->A : {hmm_matched}/"
            f"{len(entries_pos)} bascules HMM matchent un départ label-A à ±{MATCH_WINDOW}j "
            f"(agrément {hmm_agreement}). Sens A->HMM : {agreement} (label A plus fin). "
            + ("Les deux méthodes CONCORDENT (HMM->A >= 0.5) -> le START est réel et le label A "
               "bien posé."
               if triangulated else
               "Concordance PARTIELLE -> chaque méthode capte une part du signal mais le timing exact "
               "reste flou (cohérent V153/V106 : départ difficile à dater précisément).")),
        "status": "RESEARCH_ONLY_NOT_TRADING",
    }
    (V164_DIR / "v164_hmm_regime.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return out

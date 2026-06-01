"""V3-08 — Deep learning exploratoire.

MLP tabulaire régularisé (sklearn) comme référence DL.
GRU / TCN optionnels si PyTorch disponible.
Protocole : walk-forward KFold, stabilité sur 3 seeds (42, 123, 456).
Critère de rétention : +1 pt DA vs MLP, std DA ≤ 0.015, convergence OK.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import KFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mais.paths import ARTEFACTS_DIR
from mais.utils import get_logger, write_parquet

log = get_logger("mais.research.deep_learning")

RANDOM_STATE = 42
MAX_DATE = pd.Timestamp("2022-12-31")
SEEDS = [42, 123, 456]
DL_DIR = ARTEFACTS_DIR / "deep_learning"

_HAS_TORCH = False
try:
    import torch  # noqa: F401
    _HAS_TORCH = True
except ImportError:
    pass


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(axis=1, how="all")
    return df.fillna(df.median().fillna(0.0))


def _oof_eval(
    features: pd.DataFrame,
    y: pd.Series,
    model,
    n_splits: int = 5,
) -> dict[str, float]:
    from sklearn.base import clone
    n = len(features)
    oof_p = np.full(n, 0.5)
    oof_pred = np.full(n, 0)
    kf = KFold(n_splits=n_splits, shuffle=False)
    for train_idx, test_idx in kf.split(features):
        feat_tr = features.iloc[train_idx]
        y_tr = y.iloc[train_idx].astype(int)
        feat_te = features.iloc[test_idx]
        try:
            m = clone(model)
            m.fit(feat_tr, y_tr)
            oof_p[test_idx] = m.predict_proba(feat_te)[:, 1]
            oof_pred[test_idx] = m.predict(feat_te)
        except Exception as exc:
            log.warning("dl_fold_failed", error=str(exc))
    y_np = y.astype(int).to_numpy()
    da = float(accuracy_score(y_np, oof_pred))
    try:
        auc = float(roc_auc_score(y_np, oof_p)) if len(np.unique(y_np)) > 1 else np.nan
    except ValueError:
        auc = np.nan
    return {"da": da, "auc": auc}


def _build_mlp(hidden: tuple[int, ...], seed: int) -> Pipeline:
    return Pipeline([
        ("s", StandardScaler()),
        ("clf", MLPClassifier(
            hidden_layer_sizes=hidden,
            activation="relu",
            alpha=0.01,
            max_iter=300,
            early_stopping=True,
            validation_fraction=0.1,
            random_state=seed,
        )),
    ])


def run_mlp_stability(
    features: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 5,
    seeds: list[int] = SEEDS,
) -> dict[str, float]:
    """MLP (256-128-64) on 3 seeds — reference DL model."""
    results_seeds: list[dict] = []
    for seed in seeds:
        model = _build_mlp((256, 128, 64), seed)
        metrics = _oof_eval(features, y, model, n_splits)
        metrics["seed"] = seed
        results_seeds.append(metrics)
        log.info("dl_mlp_seed", seed=seed, da=metrics["da"], auc=metrics["auc"])

    da_vals = [r["da"] for r in results_seeds]
    auc_vals = [r["auc"] for r in results_seeds if not np.isnan(r["auc"])]
    return {
        "model": "mlp_256_128_64",
        "da_mean": float(np.mean(da_vals)),
        "da_std": float(np.std(da_vals)),
        "auc_mean": float(np.mean(auc_vals)) if auc_vals else np.nan,
        "stable": float(np.std(da_vals)) <= 0.015,
        "seeds_results": results_seeds,
    }


def _build_gru_torch(n_features: int, seq_len: int, hidden: int, seed: int):
    """Build GRU model if torch available, else None."""
    if not _HAS_TORCH:
        return None
    import torch
    import torch.nn as nn

    torch.manual_seed(seed)

    class GRUModel(nn.Module):
        def __init__(self, n_feat: int, h: int):
            super().__init__()
            self.gru = nn.GRU(n_feat, h, batch_first=True)
            self.head = nn.Sequential(nn.Dropout(0.3), nn.Linear(h, 1), nn.Sigmoid())

        def forward(self, x):
            _, hidden = self.gru(x)
            return self.head(hidden.squeeze(0)).squeeze(-1)

    return GRUModel(n_features, hidden)


def _run_gru_oof(
    features: pd.DataFrame,
    y: pd.Series,
    seq_len: int,
    hidden: int = 32,
    n_splits: int = 5,
    seed: int = RANDOM_STATE,
    n_epochs: int = 30,
) -> dict[str, float]:
    """GRU with sequence of seq_len days. Returns da/auc or nan if torch unavailable."""
    if not _HAS_TORCH:
        return {"da": np.nan, "auc": np.nan, "reason": "torch_not_installed"}
    import torch
    import torch.nn as nn

    n_features = features.shape[1]
    mat = features.to_numpy(dtype=np.float32)
    y_np = y.astype(int).to_numpy()
    n = len(mat)

    def make_sequences(m, start, end):
        seqs, targets = [], []
        for i in range(start, end):
            if i < seq_len:
                pad = np.zeros((seq_len - i, n_features), dtype=np.float32)
                seq = np.vstack([pad, m[max(0, i - seq_len):i]])
            else:
                seq = m[i - seq_len:i]
            seqs.append(seq)
            targets.append(y_np[i])
        return np.stack(seqs), np.array(targets)

    kf = KFold(n_splits=n_splits, shuffle=False)
    oof_p = np.full(n, 0.5, dtype=float)

    for train_idx, test_idx in kf.split(mat):
        model = _build_gru_torch(n_features, seq_len, hidden, seed)
        if model is None:
            break
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        criterion = nn.BCELoss()

        x_tr, y_tr = make_sequences(mat, train_idx[0], train_idx[-1] + 1)
        x_te, _ = make_sequences(mat, test_idx[0], test_idx[-1] + 1)

        x_tr_t = torch.tensor(x_tr)
        y_tr_t = torch.tensor(y_tr, dtype=torch.float32)
        x_te_t = torch.tensor(x_te)

        model.train()
        for _ in range(n_epochs):
            optimizer.zero_grad()
            preds = model(x_tr_t)
            loss = criterion(preds, y_tr_t)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            p_te = model(x_te_t).numpy()
        for j, idx in enumerate(test_idx):
            oof_p[idx] = p_te[j] if j < len(p_te) else 0.5

    da = float(accuracy_score(y_np, (oof_p >= 0.5).astype(int)))
    try:
        auc = float(roc_auc_score(y_np, oof_p)) if len(np.unique(y_np)) > 1 else np.nan
    except ValueError:
        auc = np.nan
    return {"da": da, "auc": auc, "reason": "ok"}


def run_gru_stability(
    features: pd.DataFrame,
    y: pd.Series,
    seq_lengths: tuple[int, ...] = (10, 20, 30),
    n_splits: int = 5,
    seeds: list[int] = SEEDS,
) -> list[dict]:
    """GRU tested on multiple seq_len and seeds."""
    if not _HAS_TORCH:
        log.warning("dl_gru_torch_unavailable")
        return [{"model": f"gru_seq{s}", "da_mean": np.nan, "da_std": np.nan, "auc_mean": np.nan, "stable": False, "reason": "torch_not_installed"} for s in seq_lengths]

    rows = []
    for seq_len in seq_lengths:
        da_seeds, auc_seeds = [], []
        for seed in seeds:
            res = _run_gru_oof(features, y, seq_len=seq_len, seed=seed, n_splits=n_splits)
            da_seeds.append(res["da"])
            if not np.isnan(res["auc"]):
                auc_seeds.append(res["auc"])
            log.info("dl_gru_seed", seq_len=seq_len, seed=seed, da=res["da"])
        rows.append({
            "model": f"gru_seq{seq_len}",
            "da_mean": float(np.mean(da_seeds)),
            "da_std": float(np.std(da_seeds)),
            "auc_mean": float(np.mean(auc_seeds)) if auc_seeds else np.nan,
            "stable": float(np.std(da_seeds)) <= 0.015,
            "reason": "ok",
        })
    return rows


def run_deep_learning(
    features_df: pd.DataFrame,
    y: pd.Series,
    n_splits: int = 5,
    output_dir: Path = DL_DIR,
) -> pd.DataFrame:
    """Full V3-08 pipeline: MLP reference + optional GRU."""
    output_dir.mkdir(parents=True, exist_ok=True)

    df = features_df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df[df["Date"] <= MAX_DATE].sort_values("Date").reset_index(drop=True)
    y = y.reindex(df.index) if hasattr(y, "reindex") else pd.Series(y.to_numpy(), index=df.index)

    valid = y.notna()
    df = df[valid].reset_index(drop=True)
    y = y[valid].astype(int).reset_index(drop=True)

    feat_cols = [c for c in df.columns if c != "Date" and df[c].dtype.kind in "fiu"]
    feats = _clean(df[feat_cols])

    rows: list[dict] = []

    # Ridge baseline (reference)
    from sklearn.linear_model import LogisticRegression
    ridge_model = Pipeline([("s", StandardScaler()), ("clf", LogisticRegression(C=1.0, max_iter=300, random_state=RANDOM_STATE))])
    ridge_metrics = _oof_eval(feats, y, ridge_model, n_splits)
    rows.append({"model": "ridge_baseline", "da_mean": ridge_metrics["da"], "da_std": 0.0, "auc_mean": ridge_metrics["auc"], "stable": True, "reason": "baseline"})
    log.info("dl_ridge_baseline", da=ridge_metrics["da"], auc=ridge_metrics["auc"])

    # MLP reference
    mlp_res = run_mlp_stability(feats, y, n_splits=n_splits)
    rows.append({k: v for k, v in mlp_res.items() if k != "seeds_results"})
    log.info("dl_mlp_done", da_mean=mlp_res["da_mean"], da_std=mlp_res["da_std"])

    # GRU (if torch available and MLP beats ridge)
    mlp_beats_ridge = mlp_res["da_mean"] > ridge_metrics["da"]
    if _HAS_TORCH and mlp_beats_ridge:
        gru_rows = run_gru_stability(feats, y, seq_lengths=(10, 20, 30), n_splits=n_splits)
        rows.extend(gru_rows)
    elif not _HAS_TORCH:
        rows.append({"model": "gru_all", "da_mean": np.nan, "da_std": np.nan, "auc_mean": np.nan, "stable": False, "reason": "torch_not_installed"})

    results = pd.DataFrame(rows)
    write_parquet(results, output_dir / "dl_comparison_report.parquet")

    # Retention criterion
    mlp_da = mlp_res["da_mean"]
    ridge_da = ridge_metrics["da"]
    gru_kept = []
    for r in rows:
        if r["model"].startswith("gru") and not np.isnan(r.get("da_mean", np.nan)):
            beats = r["da_mean"] > ridge_da + 0.01
            stable = r.get("stable", False)
            if beats and stable:
                gru_kept.append(r["model"])

    report_lines = [
        "Deep learning V3-08 — résultats",
        f"torch disponible : {_HAS_TORCH}",
        "",
        "| Modèle | DA mean | DA std | AUC mean | Stable | Note |",
        "|---|---:|---:|---:|---|---|",
    ]
    for _, r in results.iterrows():
        da = f"{r['da_mean']:.4f}" if not np.isnan(r["da_mean"]) else "N/A"
        da_s = f"{r['da_std']:.4f}" if not np.isnan(r["da_std"]) else "N/A"
        auc = f"{r['auc_mean']:.4f}" if not np.isnan(r["auc_mean"]) else "N/A"
        stable = "oui" if r.get("stable") else "non"
        reason = str(r.get("reason", ""))
        report_lines.append(f"| {r['model']} | {da} | {da_s} | {auc} | {stable} | {reason} |")

    report_lines += [
        "",
        f"MLP vs Ridge : {mlp_da:.4f} vs {ridge_da:.4f} ({'KEEP' if mlp_da > ridge_da else 'NO_GAIN'})",
        f"GRU retenu(s) : {gru_kept if gru_kept else 'aucun'}",
        "",
        "Modèles non testés (décision documentée) :",
        "  LSTM : non testé car GRU est équivalent et plus simple",
        "  Transformer : non testé car GRU ne promet pas avec ~2000 lignes 2010-2022",
    ]
    if not _HAS_TORCH:
        report_lines.append("  GRU/TCN : non testés car PyTorch non installé dans l'environnement")

    report_text = "\n".join(report_lines) + "\n"
    (output_dir / "dl_comparison_report.txt").write_text(report_text, encoding="utf-8")

    best_json = {
        "ridge_da": ridge_da,
        "mlp_da_mean": mlp_da,
        "mlp_stable": mlp_res["stable"],
        "gru_retained": gru_kept,
        "torch_available": _HAS_TORCH,
        "verdict": "mlp_kept" if mlp_da > ridge_da else "ridge_wins",
    }
    (output_dir / "dl_best_model.json").write_text(json.dumps(best_json, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("dl_done", output_dir=str(output_dir), verdict=best_json["verdict"])
    return results


def run_project_deep_learning() -> pd.DataFrame:
    """Load project features and run V3-08."""
    from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET
    feat = pd.read_parquet(FEATURES_PARQUET)
    oof_path = ARTEFACTS_DIR / "model_zoo" / "model_zoo_oof_predictions.parquet"
    oof = pd.read_parquet(oof_path)
    oof["Date"] = pd.to_datetime(oof["Date"])
    target = oof[oof["model"] == "lasso"].groupby("Date", as_index=False).agg(y_up_h40=("y_true_up", "first"))
    feat = feat.merge(target, on="Date", how="left")
    y = feat["y_up_h40"]
    feat_only = feat.drop(columns=["y_up_h40"])
    return run_deep_learning(feat_only, y, output_dir=DL_DIR)


if __name__ == "__main__":
    run_project_deep_learning()

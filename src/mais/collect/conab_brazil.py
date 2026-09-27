"""CONAB — relevés mensuels de la récolte brésilienne de maïs (1ª/2ª safrinha/3ª), point-in-time.

Source ouverte : portaldeinformacoes.conab.gov.br/downloads/arquivos/LevantamentoGraos.txt (tous les
relevés depuis 2017/18). Le relevé k de la campagne AAAA/AA paraît en (octobre AAAA + k−1), 2e semaine
(jeudi, ≤ 15) → daté au 16 du mois (conservateur), shift(1) dans build_features.
"""

from __future__ import annotations

import io
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import INTERIM_DIR
from mais.utils import get_logger

log = get_logger("mais.collect.conab")

URL = "https://portaldeinformacoes.conab.gov.br/downloads/arquivos/LevantamentoGraos.txt"
RELEASE_DAY = 16


def release_date(ano_agricola: str, lev: int) -> pd.Timestamp:
    start = int(ano_agricola[:4])
    return pd.Timestamp(start, 10, RELEASE_DAY) + pd.DateOffset(months=lev - 1)


def build_surveys(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    for c in df.columns:
        if pd.api.types.is_string_dtype(df[c]):
            df[c] = df[c].str.strip()
    m = df[df["produto"] == "MILHO"].copy()
    m["lev"] = pd.to_numeric(m["id_levantamento"]).astype(int)
    m["prod"] = pd.to_numeric(m["producao_mil_t"], errors="coerce")
    tot = m.groupby(["ano_agricola", "lev"])["prod"].sum().rename("br_conab_corn_kt")
    safr = m[m["safra"].str.startswith("2")].groupby(["ano_agricola", "lev"])["prod"].sum()
    out = pd.concat([tot, safr.rename("br_conab_safrinha_kt")], axis=1).reset_index()
    dates = [release_date(a, k) for a, k in zip(out["ano_agricola"], out["lev"], strict=True)]
    out["Date"] = pd.to_datetime(dates)
    return out.sort_values("Date").reset_index(drop=True)


def build_features(surveys: pd.DataFrame) -> pd.DataFrame:
    s = surveys.copy()
    s["br_conab_corn_rev_kt"] = s.groupby("ano_agricola")["br_conab_corn_kt"].diff()
    last_prev = s.groupby("ano_agricola")["br_conab_corn_kt"].last().shift(1)
    s["br_conab_corn_vs_prev_crop_pct"] = (
        s["br_conab_corn_kt"] / s["ano_agricola"].map(last_prev) - 1) * 100
    s["br_conab_safrinha_share"] = s["br_conab_safrinha_kt"] / s["br_conab_corn_kt"].replace(0, np.nan)
    cols = ["Date", "br_conab_corn_kt", "br_conab_safrinha_kt", "br_conab_corn_rev_kt",
            "br_conab_corn_vs_prev_crop_pct", "br_conab_safrinha_share"]
    return s[cols]


def download(out_dir: Path, src: dict) -> str:
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (research; etude-mais)"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        text = resp.read().decode("latin1")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "LevantamentoGraos.txt").write_text(text, encoding="utf-8")
    surveys = build_surveys(pd.read_csv(io.StringIO(text), sep=";"))
    feats = build_features(surveys)
    feats = feats[feats["Date"] <= pd.Timestamp.today().normalize()]
    feats.to_parquet(INTERIM_DIR / "conab_brazil.parquet", index=False)
    log.info("conab_saved", surveys=len(feats), last=str(feats["Date"].max().date()))
    return f"{len(feats)} relevés, dernier {feats['Date'].max().date()}"

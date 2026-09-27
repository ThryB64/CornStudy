"""Archive append-only des contrats CBOT maïs (ZC H/K/N/U/Z) cotés sur Yahoo.

Yahoo ne sert que les contrats vivants (historique depuis leur listing) et efface les expirés :
chaque passage fusionne l'historique complet des contrats vivants dans data/raw/cbot_curve/contracts.parquet.
Un passage tous les ~2 mois suffit à ne perdre aucun contrat. Pas encore branché aux features
(historique < 4 ans) : accumulation pour la future étude de courbe / carry.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from mais.paths import DATA_DIR
from mais.utils import get_logger

log = get_logger("mais.collect.cbot_curve")

# copie commitée par le workflow hebdo GitHub (indépendante du PC) ; la copie locale la fusionne
CI_ARCHIVE = DATA_DIR / "official_forward" / "cbot_curve_contracts.parquet"
MONTHS = {"H": 3, "K": 5, "N": 7, "U": 9, "Z": 12}
N_YEARS_AHEAD = 3


def live_contracts(today: date | None = None) -> list[tuple[str, pd.Timestamp]]:
    today = today or date.today()
    out = []
    for year in range(today.year, today.year + N_YEARS_AHEAD + 1):
        for code, month in MONTHS.items():
            expiry = pd.Timestamp(year, month, 15)
            if expiry >= pd.Timestamp(today) - pd.Timedelta(days=20):
                out.append((f"ZC{code}{str(year)[-2:]}", expiry))
    return out


def _download(symbol: str) -> pd.DataFrame:
    import yfinance as yf

    data = yf.download(f"{symbol}.CBT", period="max", progress=False, auto_adjust=False)
    if data is None or data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        data = data.droplevel(1, axis=1)
    df = data.reset_index().rename(columns={"Date": "Date", "Close": "close", "Volume": "volume"})
    return df[["Date", "close", "volume"]].dropna(subset=["close"])


def download(out_dir: Path, src: dict) -> str:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = Path(src["out_path"]) if src.get("out_path") else out_dir / "contracts.parquet"
    olds = [pd.read_parquet(p) for p in {path, CI_ARCHIVE} if p.exists()]
    old = pd.concat(olds, ignore_index=True) if olds else pd.DataFrame()
    frames, got = [], 0
    for symbol, expiry in live_contracts():
        df = _download(symbol)
        if df.empty:
            continue
        frames.append(df.assign(contract=symbol, delivery_month=expiry.strftime("%Y-%m")))
        got += 1
    if not frames:
        raise RuntimeError("aucun contrat ZC récupéré")
    new = pd.concat([old, *frames], ignore_index=True)
    new["Date"] = pd.to_datetime(new["Date"]).dt.normalize()
    new = new.drop_duplicates(["contract", "Date"], keep="last").sort_values(["Date", "delivery_month"])
    new.to_parquet(path, index=False)
    log.info("cbot_curve_saved", contracts=got, rows=len(new), n_contracts=new["contract"].nunique())
    return f"{got} contrats vivants, {new['contract'].nunique()} archivés, {len(new)} lignes"

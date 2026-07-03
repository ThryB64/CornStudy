"""Features anti-fuite du score de vente CBOT (étape 7).

Port des seuls encodages validés (étapes 4-6) dans le paquet principal, depuis les
mêmes sources internes : prix CBOT (`data/interim/market.parquet`), Crop Condition NASS
(`data/raw/usda_nass_crop_condition/crop_progress.parquet`), WASDE vintage publication-only
(EXT026, lu en lecture seule). Toutes les transformations sont passé-only : z/percentiles
expandants `shift(1)`, anomalies vs climatologie des années passées, lags de publication
réels (WASDE +1 jour ouvré ; Crop Condition lundi → mardi). La cible directionnelle utilise
la **vraie ligne de marché** `index[i+h]`, jamais `date + h jours calendaires`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from mais.paths import INTERIM_DIR, PROJECT_ROOT, RAW_DIR

WASDE_VINTAGE = (PROJECT_ROOT / "external_research" / "results" / "external_tests" /
                 "EXT026_wasde_vintage_pipeline" / "wasde_vintage_dataset.csv")
CROP_PARQUET = RAW_DIR / "usda_nass_crop_condition" / "crop_progress.parquet"
MARKET_PARQUET = INTERIM_DIR / "market.parquet"

BASE_COLS = ["base_sin", "base_cos"]


# --- helpers passé-only (port de series_utils) --------------------------------

def _daily_ffill(df: pd.DataFrame, end: str = "2026-12-31") -> pd.DataFrame:
    full = pd.date_range(df.index.min(), pd.Timestamp(end), freq="D")
    return df.reindex(df.index.union(full)).sort_index().ffill().reindex(full)


def _expanding_z(s: pd.Series, min_periods: int = 12) -> pd.Series:
    m = s.expanding(min_periods=min_periods).mean().shift(1)
    sd = s.expanding(min_periods=min_periods).std().shift(1)
    return (s - m) / sd


def _expanding_pctile(s: pd.Series, min_periods: int = 12) -> pd.Series:
    vals = s.to_numpy(float)
    out = np.full(len(vals), np.nan)
    for i in range(min_periods, len(vals)):
        past = vals[:i][np.isfinite(vals[:i])]
        if len(past) >= min_periods and np.isfinite(vals[i]):
            out[i] = (past < vals[i]).mean()
    return pd.Series(out, index=s.index)


def _weekofyear_anom(s: pd.Series, min_years: int = 4) -> pd.Series:
    df = pd.DataFrame({"x": s.to_numpy(float)}, index=s.index)
    df["woy"] = df.index.isocalendar().week.to_numpy()
    out = pd.Series(np.nan, index=s.index)
    for _woy, g in df.groupby("woy"):
        g = g.sort_index()
        mean = g["x"].expanding().mean().shift(1)
        std = g["x"].expanding().std().shift(1)
        cnt = g["x"].expanding().count().shift(1)
        z = ((g["x"] - mean) / std).where(cnt >= min_years)
        out.loc[g.index] = z.to_numpy()
    return out


# --- cible directionnelle anti-fuite ------------------------------------------

def target_dates_from_index(index: pd.DatetimeIndex, h: int) -> pd.Series:
    """Vraie date de la cible : index[i+h] (lignes de marché), PAS date + h jours."""
    return pd.Series(index, index=index).shift(-h)


def direction_target(px: pd.Series, h: int) -> pd.Series:
    """Signe du log-retour t -> t+h (1=hausse, 0=baisse), NaN si pas de futur."""
    logp = np.log(px)
    fwd = logp.shift(-h) - logp
    return (fwd > 0).astype(float).where(fwd.notna())


def logret_target(px: pd.Series, h: int) -> pd.Series:
    logp = np.log(px)
    return logp.shift(-h) - logp


# --- sources -------------------------------------------------------------------

def load_market() -> pd.DataFrame:
    m = pd.read_parquet(MARKET_PARQUET)
    m["Date"] = pd.to_datetime(m["Date"])
    m = m.sort_values("Date").set_index("Date")
    px = m["corn_close"].astype(float)
    logp = np.log(px)
    out = pd.DataFrame(index=m.index)
    out["corn_close"] = px
    out["logret"] = logp.diff()
    # momentum marché : sert UNIQUEMENT de baseline "marché seul" (hors score)
    out["base_ret_5d"] = logp.diff(5)
    out["base_ret_20d"] = logp.diff(20)
    out["base_vol_20"] = logp.diff().rolling(20).std()
    doy = out.index.dayofyear.to_numpy()
    out["base_sin"] = np.sin(2 * np.pi * doy / 365.25)
    out["base_cos"] = np.cos(2 * np.pi * doy / 365.25)
    return out


def wasde_features() -> tuple[pd.DataFrame, dict]:
    w = pd.read_csv(WASDE_VINTAGE)
    w["available_from"] = pd.to_datetime(w["available_from"])
    w = w.sort_values("available_from").reset_index(drop=True)
    s2u = w["stocks_to_use_ratio"]
    ev = pd.DataFrame(index=w["available_from"])
    ev["s2u_z"] = _expanding_z(s2u, 12).to_numpy()
    ev["s2u_pctile"] = _expanding_pctile(s2u, 12).to_numpy()
    ev["s2u_slow_chg"] = s2u.diff(3).to_numpy()
    feats = _daily_ffill(ev[~ev.index.duplicated(keep="last")])
    fdict = {
        "s2u_z": "z-score expandant du stocks-to-use WASDE (vintage publication+1BD)",
        "s2u_pctile": "percentile expandant du stocks-to-use",
        "s2u_slow_chg": "variation lente du bilan (3 rapports)",
    }
    return feats, fdict


def crop_features() -> tuple[pd.DataFrame, dict]:
    cp = pd.read_parquet(CROP_PARQUET)
    cp["Date"] = pd.to_datetime(cp["Date"])
    cp = cp.sort_values("Date").set_index("Date")
    cp = cp[cp.index.year >= 1995]
    f = pd.DataFrame(index=cp.index)
    f["cond_gd_ex_anom"] = _weekofyear_anom(cp["condition_gd_ex_pct"])
    f["cond_dev5y"] = cp["condition_gd_ex_pct"] - \
        cp["condition_gd_ex_pct"].rolling(52 * 5, min_periods=52).mean().shift(1)
    f["cond_poor_vp"] = cp["condition_poor_vp_pct"]
    f.index = f.index + pd.Timedelta(days=2)        # publication lundi -> dispo mardi
    feats = _daily_ffill(f)
    fdict = {
        "cond_gd_ex_anom": "anomalie z good+excellent vs climatologie par semaine (passé)",
        "cond_dev5y": "écart good+excellent vs moyenne 5 ans passée",
        "cond_poor_vp": "condition poor+very-poor (%)",
    }
    return feats, fdict


def har_vol_features(logret: pd.Series) -> tuple[pd.DataFrame, dict]:
    """Composantes HAR (vol réalisée passée 5/22/66 j) sur le calendrier marché."""
    r = logret.dropna()

    def past_rv(window: int) -> pd.Series:
        return np.sqrt((r ** 2).rolling(window).sum())

    f = pd.DataFrame(index=r.index)
    f["rv_w"] = past_rv(5)
    f["rv_m"] = past_rv(22)
    f["rv_q"] = past_rv(66)
    fdict = {"rv_w": "vol réalisée passée 5 j", "rv_m": "vol réalisée passée 22 j",
             "rv_q": "vol réalisée passée 66 j"}
    return f, fdict


def future_realized_vol(logret: pd.Series, h: int) -> pd.Series:
    """Vol réalisée h-jours forward (pour l'éval du risque, pas pour le score)."""
    r2 = logret ** 2
    fwd = r2.shift(-1).rolling(h).sum().shift(-(h - 1))
    return np.sqrt(fwd)


def regime_features(mkt: pd.DataFrame, wasde: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Régimes passé-only (confiance seulement). uptrend / low_vol / bilan extrême."""
    logp = np.log(mkt["corn_close"])
    r = logp.diff()
    reg = pd.DataFrame(index=mkt.index)
    rv20 = r.rolling(20).std()
    reg["regime_low_vol"] = (rv20 <= rv20.expanding(252).median().shift(1)).astype(float)
    reg["regime_uptrend"] = (logp.diff(120) > 0.02).astype(float)
    s2up = wasde["s2u_pctile"].reindex(mkt.index).ffill()
    reg["regime_bilan_extreme"] = ((s2up < 0.33) | (s2up > 0.66)).astype(float)
    fdict = {
        "regime_low_vol": "régime faible volatilité (rv20 <= médiane expandante)",
        "regime_uptrend": "régime haussier (momentum 120 j > 0.02)",
        "regime_bilan_extreme": "bilan tendu ou large (percentile s2u <0.33 ou >0.66)",
    }
    return reg, fdict


def build_frame() -> tuple[pd.DataFrame, dict]:
    """DataFrame quotidien sur le calendrier marché avec toutes les features validées."""
    mkt = load_market()
    wf, wd = wasde_features()
    cf, cd = crop_features()
    hf, hd = har_vol_features(mkt["logret"])
    rf, rdc = regime_features(mkt, wf)
    df = mkt.join(wf.reindex(mkt.index).ffill())
    df = df.join(cf.reindex(mkt.index).ffill())
    df = df.join(hf.reindex(mkt.index))
    df = df.join(rf)
    fdict = {**wd, **cd, **hd, **rdc,
             "base_sin": "saisonnalité (sin jour de l'année)",
             "base_cos": "saisonnalité (cos jour de l'année)"}
    return df, fdict

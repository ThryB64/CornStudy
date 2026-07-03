"""EXT004 — Crush ethanol / energie (PARTIAL_DATA).

Donnees disponibles : EIA ethanol production + stocks (hebdo vendredi, publie
mercredi -> available = Date+5j) ; petrole (oil_close) et gaz (gas_close)
quotidiens ; corn_close. ABSENTS : prix ethanol (CME/EIA), DDG, soybean meal ->
pas de vraie marge crush ni de ratio corn/ethanol. On teste des PROXYS :
demande ethanol (production/stocks) + ratios energie-corn. Variable d'etat lente
(H40-H90), pas un signal court (cf. fiche EXT004 : H60+).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_common"))
import ext_harness as H  # noqa: E402
import series_utils as S  # noqa: E402

EXP, DIRN = "EXT004", "EXT004_ethanol_ddg_crush_spread"


def build_features():
    eth = pd.read_parquet(H.DATA / "interim" / "eia_ethanol.parquet")
    eth["Date"] = pd.to_datetime(eth["Date"])
    eth = eth.sort_values("Date").set_index("Date")
    ew = pd.DataFrame(index=eth.index)
    ew["eth_prod_z"] = S.expanding_z(eth["ethanol_production_kbd"])
    ew["eth_prod_yoy"] = eth["ethanol_production_kbd"].pct_change(52)
    ew["eth_stocks_z"] = S.expanding_z(eth["ethanol_stocks_kbbl"])
    ew["eth_stocks_chg"] = eth["ethanol_stocks_kbbl"].diff()
    ew.index = ew.index + pd.Timedelta(days=5)  # EIA publie mercredi suivant
    eth_daily = S.daily_ffill(ew, end="2025-12-31")

    mk = pd.read_parquet(H.DATA / "interim" / "market.parquet")
    mk["Date"] = pd.to_datetime(mk["Date"])
    mk = mk.sort_values("Date").set_index("Date")
    md = pd.DataFrame(index=mk.index)
    with np.errstate(divide="ignore", invalid="ignore"):
        md["oil_corn_ratio"] = mk["oil_close"] / mk["corn_close"]
        md["gas_corn_ratio"] = mk["gas_close"] / mk["corn_close"]
    md["oil_corn_z"] = S.expanding_z(md["oil_corn_ratio"], min_periods=250)
    md["gas_corn_z"] = S.expanding_z(md["gas_corn_ratio"], min_periods=250)
    md = md[["oil_corn_z", "gas_corn_z"]]

    feats = eth_daily.join(md, how="outer").ffill()
    fdict = {
        "eth_prod_z": "z-score expandant production ethanol (demande corn)",
        "eth_prod_yoy": "Variation YoY production ethanol",
        "eth_stocks_z": "z-score expandant stocks ethanol",
        "eth_stocks_chg": "Variation hebdo stocks ethanol",
        "oil_corn_z": "z-score ratio petrole/corn (proxy energie-corn)",
        "gas_corn_z": "z-score ratio gaz/corn (proxy cout/energie-corn)",
    }
    return feats, list(feats.columns), fdict


def main():
    feats, cols, fdict = build_features()
    out = H.RESULTS / DIRN
    out.mkdir(parents=True, exist_ok=True)
    feats.dropna(how="all").to_csv(out / "ethanol_ddg_features.csv")
    met = H.evaluate_family(EXP, DIRN, feats, cols, feature_dictionary=fdict)
    print(met[met.model == "DELTA"][["horizon", "rmse_pct", "da", "dm_pvalue", "n"]].to_string())
    print("verdict:", H.verdict_from_delta(met))


if __name__ == "__main__":
    main()

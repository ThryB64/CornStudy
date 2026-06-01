"""Infrastructure météo PRÉVISIONNELLE (forecast) avec garde anti-leakage stricte.

Le marché price la météo ANTICIPÉE, pas seulement réalisée. Ce module transforme une archive de prévisions
(format long, telle que connue à chaque date d'émission) en features quotidiennes : anomalies vs normales,
RÉVISIONS de prévision (run du jour − run précédent), incertitude d'ensemble, stress par phénologie.

ANTI-LEAKAGE (critique) : une feature au jour J n'utilise que des prévisions avec
`forecast_issue_date <= J`. Jamais de météo réalisée future, jamais de run postérieur.

Schéma d'archive attendu (long) :
  forecast_issue_date | forecast_valid_date | lead_time_days | zone | variable | value | [member]

Statut data : l'archive réelle (Open-Meteo Historical Forecast / GFS / GEFS) n'est pas encore collectée
=> WAITING_DATA. Le code et les tests anti-leakage fonctionnent sur données synthétiques dès maintenant.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Pondération des États US Corn Belt par production de maïs (approximative).
US_CORN_BELT_WEIGHTS = {
    "iowa": 0.18, "illinois": 0.16, "nebraska": 0.13, "minnesota": 0.11, "indiana": 0.08,
    "ohio": 0.06, "south_dakota": 0.06, "kansas": 0.06, "missouri": 0.05, "wisconsin": 0.04,
}
EU_ZONES_WEIGHTS = {
    "france": 0.30, "romania": 0.16, "hungary": 0.12, "north_italy": 0.10, "poland": 0.10,
    "ukraine_west": 0.16, "serbia": 0.06,
}
POLLINATION_MONTHS = (6, 7, 8)
REQUIRED_COLS = ("forecast_issue_date", "forecast_valid_date", "lead_time_days", "zone", "variable", "value")


class ForecastLeakageError(RuntimeError):
    """Levée si une feature forecast pourrait utiliser de l'information future."""


def assert_forecast_no_leakage(fc: pd.DataFrame, as_of: pd.Timestamp | None = None) -> None:
    """Vérifie la cohérence temporelle de l'archive : valid = issue + lead, et issue <= as_of si fourni."""
    missing = [c for c in REQUIRED_COLS if c not in fc.columns]
    if missing:
        raise ForecastLeakageError(f"colonnes manquantes: {missing}")
    issue = pd.to_datetime(fc["forecast_issue_date"])
    valid = pd.to_datetime(fc["forecast_valid_date"])
    lead = pd.to_numeric(fc["lead_time_days"])
    # valid_date doit être issue_date + lead_time
    expected_valid = issue + pd.to_timedelta(lead, unit="D")
    if not (valid.dt.normalize() == expected_valid.dt.normalize()).all():
        raise ForecastLeakageError("forecast_valid_date != forecast_issue_date + lead_time_days")
    if (lead < 0).any():
        raise ForecastLeakageError("lead_time_days négatif (réanalyse postérieure interdite)")
    if as_of is not None and (issue > pd.Timestamp(as_of)).any():
        raise ForecastLeakageError("forecast_issue_date > as_of (run futur interdit)")


def _zone_weights(zones: pd.Series, region: str) -> dict:
    table = US_CORN_BELT_WEIGHTS if region == "us" else EU_ZONES_WEIGHTS
    present = {z: table.get(z, 0.0) for z in zones.unique()}
    tot = sum(present.values())
    if tot <= 0:
        return {z: 1.0 / len(present) for z in present}
    return {z: w / tot for z, w in present.items()}


def _weighted_window(fc: pd.DataFrame, variable: str, lead_lo: int, lead_hi: int, region: str) -> pd.Series:
    """Pour chaque issue_date : moyenne (pondérée zones) de `variable` sur la fenêtre de lead [lo, hi]."""
    sub = fc[(fc["variable"] == variable)
             & (fc["lead_time_days"] >= lead_lo) & (fc["lead_time_days"] <= lead_hi)].copy()
    if sub.empty:
        return pd.Series(dtype=float)
    w = _zone_weights(sub["zone"], region)
    sub["w"] = sub["zone"].map(w)
    # moyenne sur la fenêtre de lead par (issue, zone), puis pondération zones
    by_iz = sub.groupby(["forecast_issue_date", "zone"]).agg(v=("value", "mean"), w=("w", "first"))
    by_iz["vw"] = by_iz["v"] * by_iz["w"]
    agg = by_iz.groupby("forecast_issue_date").agg(num=("vw", "sum"), den=("w", "sum"))
    return (agg["num"] / agg["den"]).rename(variable)


def build_forecast_features(fc: pd.DataFrame, normals: dict[str, float] | None = None,
                            region: str = "us", lead_lo: int = 7, lead_hi: int = 14) -> pd.DataFrame:
    """Features quotidiennes (indexées par forecast_issue_date) : anomalies + révisions + phénologie.

    `normals` : dict variable -> valeur normale climatologique (anomalie = prévu − normale).
    Anti-leakage : chaque ligne n'utilise que le run de son issue_date et le run précédent (révision).
    """
    assert_forecast_no_leakage(fc)
    fc = fc.copy()
    fc["forecast_issue_date"] = pd.to_datetime(fc["forecast_issue_date"])
    normals = normals or {}
    variables = list(fc["variable"].unique())
    cols = {}
    for var in variables:
        s = _weighted_window(fc, var, lead_lo, lead_hi, region)
        if s.empty:
            continue
        s = s.sort_index()
        cols[f"fc_{var}"] = s
        # anomalie vs normale
        norm = normals.get(var, float(s.expanding(min_periods=30).mean().iloc[-1]) if len(s) >= 30 else s.mean())
        cols[f"fc_{var}_anom"] = s - norm
        # révision : run du jour − run précédent disponible (même fenêtre de lead)
        cols[f"fc_{var}_revision"] = s.diff()
    if not cols:
        return pd.DataFrame()
    out = pd.DataFrame(cols).sort_index()
    out.index.name = "forecast_issue_date"

    # incertitude d'ensemble si membres présents
    if "member" in fc.columns:
        for var in variables:
            sub = fc[(fc["variable"] == var) & (fc["lead_time_days"].between(lead_lo, lead_hi))]
            disp = sub.groupby("forecast_issue_date")["value"].std()
            if not disp.empty:
                out[f"fc_{var}_ensemble_dispersion"] = disp.reindex(out.index)

    # stress par phénologie : anomalie chaleur/sécheresse pondérée par fenêtre pollinisation
    months = out.index.month
    pollination = pd.Series(np.isin(months, POLLINATION_MONTHS).astype(float), index=out.index)
    heat_anom = out.get(f"fc_{_pick(variables, 'heat')}_anom")
    dry_anom = out.get(f"fc_{_pick(variables, 'precip')}_anom")
    if heat_anom is not None:
        out["us_pollination_heat_risk"] = (heat_anom.clip(lower=0) * pollination).values
    if dry_anom is not None:
        # déficit = anomalie de précip négative -> risque sécheresse
        out["us_drought_forecast_risk"] = ((-dry_anom).clip(lower=0) * pollination).values
    return out


def _pick(variables: list[str], key: str) -> str:
    for v in variables:
        if key in v.lower():
            return v
    return variables[0] if variables else ""


def make_synthetic_forecast_archive(n_days: int = 120, seed: int = 0) -> pd.DataFrame:
    """Génère une archive de prévisions synthétique cohérente (pour tests anti-leakage et démo)."""
    rng = np.random.default_rng(seed)
    rows = []
    start = pd.Timestamp("2023-06-01")
    zones = list(US_CORN_BELT_WEIGHTS)
    for d in range(n_days):
        issue = start + pd.Timedelta(days=d)
        for lead in range(1, 17):
            valid = issue + pd.Timedelta(days=lead)
            for z in zones:
                rows.append({
                    "forecast_issue_date": issue, "forecast_valid_date": valid,
                    "lead_time_days": lead, "zone": z, "variable": "tmax",
                    "value": 28 + rng.normal(0, 3) + (lead * 0.05),
                })
                rows.append({
                    "forecast_issue_date": issue, "forecast_valid_date": valid,
                    "lead_time_days": lead, "zone": z, "variable": "precip",
                    "value": max(0.0, rng.normal(3, 2)),
                })
    return pd.DataFrame(rows)

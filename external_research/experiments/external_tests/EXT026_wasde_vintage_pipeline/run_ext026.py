"""EXT026 — Audit anti-fuite WASDE + construction du dataset vintage.

1) Audit: les valeurs de data/interim/wasde.parquet changent-elles a la vraie
   date de publication (links table / calendrier USDA) ou avant (fuite) ?
2) Vintage: csv/wasde/wasde_txt.csv (valeurs par rapport, archive interne de
   210 txt USDA Cornell) x vraies dates de publication -> dataset date
   publication, disponible au jour ouvre suivant (regle conservatrice,
   publication 12h ET intra-seance).

Aucune ecriture hors de external_research/results/external_tests/.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
RESULTS = ROOT / "external_research" / "results" / "external_tests" / \
    "EXT026_wasde_vintage_pipeline"

VARS = ["area_planted", "area_harvested", "yield_per_acre", "production",
        "beginning_stocks", "ending_stocks", "stocks_to_use_ratio", "imports",
        "supply_total", "feed_and_residual", "food_seed_industrial",
        "ethanol_byproducts", "domestic_total", "exports", "use_total",
        "avg_farm_price"]


def load_publication_dates() -> pd.DataFrame:
    """Meilleure date de publication par rapport: links_table (URL Cornell)
    > usda_calendar (is_wasde_day du mois du rapport) > fallback jour 12."""
    txt = pd.read_csv(ROOT / "csv" / "wasde" / "wasde_txt.csv")
    base = txt[["filename", "report_date"]].copy()
    base["report_date"] = pd.to_datetime(base["report_date"])

    links = pd.read_csv(ROOT / "csv" / "wasde" / "wasde_links_table.csv")
    links["pub_links"] = pd.to_datetime(links["date"])
    base = base.merge(links[["filename", "pub_links"]], on="filename", how="left")

    cal = pd.read_parquet(ROOT / "data" / "interim" / "usda_calendar.parquet")
    cal["Date"] = pd.to_datetime(cal["Date"])
    wdays = cal.loc[cal["is_wasde_day"] == 1, "Date"]
    cal_map = {(d.year, d.month): d for d in wdays}
    base["pub_calendar"] = [
        cal_map.get((d.year, d.month), pd.NaT) for d in base["report_date"]]

    base["publication_date"] = base["pub_links"]
    base["pub_date_source"] = np.where(base["pub_links"].notna(), "links_table", "")
    use_cal = base["publication_date"].isna() & base["pub_calendar"].notna()
    base.loc[use_cal, "publication_date"] = base.loc[use_cal, "pub_calendar"]
    base.loc[use_cal, "pub_date_source"] = "usda_calendar"
    still = base["publication_date"].isna()
    base.loc[still, "publication_date"] = base.loc[still, "report_date"] + pd.offsets.Day(11)
    base.loc[still, "pub_date_source"] = "fallback_day12"

    both = base.dropna(subset=["pub_links", "pub_calendar"])
    base.attrs["n_disagree_sources"] = int(
        (both["pub_links"].dt.normalize() != both["pub_calendar"].dt.normalize()).sum())
    base.attrs["n_both"] = len(both)
    return base[["filename", "report_date", "publication_date", "pub_date_source"]]


def audit_current(pub: pd.DataFrame) -> pd.DataFrame:
    """Date de premier changement de wasde_production dans la serie quotidienne
    vs vraie date de publication du rapport correspondant."""
    daily = pd.read_parquet(ROOT / "data" / "interim" / "wasde.parquet")
    daily["Date"] = pd.to_datetime(daily["Date"])
    daily = daily.sort_values("Date").reset_index(drop=True)

    sig = daily[["wasde_production", "wasde_ending_stocks", "wasde_exports"]]
    changed = (sig != sig.shift(1)).any(axis=1)
    changed.iloc[0] = False
    change_dates = daily.loc[changed, "Date"].reset_index(drop=True)

    pubs = pub[pub["pub_date_source"].isin(["links_table", "usda_calendar"])]
    pubs = pubs.sort_values("publication_date").reset_index(drop=True)
    rows = []
    for _, p in pubs.iterrows():
        after = change_dates[(change_dates >= p["publication_date"] - pd.Timedelta(days=45)) &
                             (change_dates <= p["publication_date"] + pd.Timedelta(days=45))]
        if after.empty:
            continue
        # changement le plus proche de la publication
        nearest = after.iloc[(after - p["publication_date"]).abs().argmin()]
        rows.append({"filename": p["filename"],
                     "publication_date": p["publication_date"],
                     "series_change_date": nearest,
                     "lag_days": (nearest - p["publication_date"]).days})
    audit = pd.DataFrame(rows)
    return audit


def build_vintage(pub: pd.DataFrame) -> pd.DataFrame:
    txt = pd.read_csv(ROOT / "csv" / "wasde" / "wasde_txt.csv")
    df = txt.drop(columns=["report_date"]).merge(pub, on="filename", how="left")
    df["publication_date"] = pd.to_datetime(df["publication_date"])

    # disponibilite: jour ouvre suivant la publication (12h ET intra-seance)
    df["available_from"] = df["publication_date"] + pd.offsets.BDay(1)

    # campagne marketing approx (rapports de sep a aout -> campagne N/N+1)
    df["report_month"] = pd.to_datetime(df["report_date"]).dt.month
    df["report_year"] = pd.to_datetime(df["report_date"]).dt.year
    my_start = np.where(df["report_month"] >= 9, df["report_year"],
                        df["report_year"] - 1)
    df["marketing_year_approx"] = [f"{y}/{y + 1}" for y in my_start]

    df["stocks_to_use_calc"] = df["ending_stocks"] / df["use_total"]

    df = df.sort_values("publication_date").reset_index(drop=True)
    for v in VARS + ["stocks_to_use_calc"]:
        if v in df.columns:
            df[f"{v}_chg_m1"] = df[v].diff()
            df[f"{v}_pct_m1"] = df[v].pct_change()

    cols = (["filename", "report_date", "publication_date", "pub_date_source",
             "available_from", "marketing_year_approx", "data_quality_score",
             "missing_variables"] + [v for v in VARS if v in df.columns] +
            ["stocks_to_use_calc"] +
            [c for c in df.columns if c.endswith(("_chg_m1", "_pct_m1"))])
    return df[cols]


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    pub = load_publication_dates()
    pub.to_csv(RESULTS / "wasde_publication_dates.csv", index=False)

    audit = audit_current(pub)
    audit.to_csv(RESULTS / "wasde_audit_lags.csv", index=False)

    neg = audit[audit["lag_days"] < 0]
    md = ["# Audit anti-fuite — WASDE quotidien interne (`data/interim/wasde.parquet`)",
          "",
          f"Rapports croisés : {len(audit)} (publication réelle ↔ date de changement de la série quotidienne).",
          "",
          f"- lag médian (changement − publication) : **{audit['lag_days'].median():.0f} jours**",
          f"- lag moyen : {audit['lag_days'].mean():.1f} jours",
          f"- rapports dont les valeurs apparaissent AVANT la publication réelle : **{len(neg)}/{len(audit)}**",
          f"- pire avance (fuite) : {audit['lag_days'].min():.0f} jours",
          f"- distribution des lags : p10={audit['lag_days'].quantile(0.1):.0f}, "
          f"p50={audit['lag_days'].median():.0f}, p90={audit['lag_days'].quantile(0.9):.0f}",
          ""]
    if len(neg):
        md += ["## FUITE DÉTECTÉE",
               "",
               "Les valeurs WASDE de la série quotidienne interne sont visibles avant",
               "leur date de publication réelle pour les rapports ci-dessous (extrait) :",
               "", neg.head(15).to_string(index=False), "",
               "Cause vraisemblable : expansion quotidienne calée sur `report_date`",
               "(1er du mois dans le parse) au lieu de la date de publication réelle",
               "(~8-12 du mois). Correction à proposer via ticket projet séparé :",
               "recaler l'expansion sur `publication_date` + 1 jour ouvré.", ""]
    else:
        md += ["## Pas de fuite détectée",
               "", "Les changements de valeurs suivent les publications réelles.", ""]
    (RESULTS / "wasde_current_audit.md").write_text("\n".join(md))

    vintage = build_vintage(pub)
    vintage.to_csv(RESULTS / "wasde_vintage_dataset.csv", index=False)

    dico = pd.DataFrame([
        {"column": "publication_date", "definition": "date de publication reelle (links table USDA Cornell)", "leakage_rule": "valeur inconnue avant cette date"},
        {"column": "available_from", "definition": "publication + 1 jour ouvre (conservateur, publication 12h ET)", "leakage_rule": "premiere date d'usage en feature quotidienne close-to-close"},
        {"column": "pub_date_source", "definition": "links_table ou fallback_day12", "leakage_rule": "fallback = jour 12 du mois, jamais avant la vraie date moyenne"},
        {"column": "marketing_year_approx", "definition": "campagne sep->aout deduite du mois de rapport", "leakage_rule": "approximation; le rapport melange old/new crop de mai a sept"},
        {"column": "production", "definition": "production US mais, million bu, telle que publiee", "leakage_rule": "vintage, jamais revisee retroactivement"},
        {"column": "ending_stocks", "definition": "stocks fin de campagne US, million bu, tels que publies", "leakage_rule": "idem"},
        {"column": "stocks_to_use_calc", "definition": "ending_stocks/use_total recalcule", "leakage_rule": "derive de valeurs vintage uniquement"},
        {"column": "*_chg_m1 / *_pct_m1", "definition": "variation vs rapport precedent (proxy de surprise EXT008)", "leakage_rule": "disponible a available_from du rapport M"},
    ])
    dico.to_csv(RESULTS / "wasde_feature_dictionary.csv", index=False)

    print(f"publications: {len(pub)} | audit: {len(audit)} rapports croisés | "
          f"fuites: {len(neg)} | lag médian: {audit['lag_days'].median():.0f}j")
    print(f"vintage: {len(vintage)} rapports, {vintage['publication_date'].min().date()} -> "
          f"{vintage['publication_date'].max().date()}")
    print(f"pub_date fallback: {(vintage['pub_date_source'] == 'fallback_day12').sum()}")
    na = vintage[VARS].notna().mean().round(2).sort_values()
    print("couverture variables (part non-NaN):")
    print(na.to_string())


if __name__ == "__main__":
    main()

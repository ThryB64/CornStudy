"""NB2-00 — Audit données EMA v2 : source, couverture, gaps et période utilisable."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, EMA_CONTRACT_DAILY, EMA_FRONT_RAW, PROJECT_ROOT

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_data_audit_v2.json"
_DOC_OUTPUT = PROJECT_ROOT / "docs" / "EMA_DATA_AUDIT_V2.md"

_MONTH_CODES = ["H", "M", "Q", "X"]
_COVERAGE_OK = 0.80
_COVERAGE_PARTIAL = 0.60


def _crop_year(date: pd.Timestamp) -> int:
    return date.year if date.month >= 10 else date.year - 1


def _business_days_in_crop_year(cy: int) -> int:
    start = pd.Timestamp(f"{cy}-10-01")
    end = pd.Timestamp(f"{cy + 1}-09-30")
    return len(pd.bdate_range(start, end))


def _coverage_matrix(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["crop_year"] = df["date"].apply(_crop_year)
    matrix: dict[int, dict[str, float]] = {}
    crop_years = sorted(df["crop_year"].unique())
    for cy in crop_years:
        expected_bdays = _business_days_in_crop_year(cy)
        row: dict[str, float] = {}
        for mc in _MONTH_CODES:
            n = len(df[(df["crop_year"] == cy) & (df["month_code"] == mc)])
            row[mc] = round(n / max(expected_bdays, 1), 3)
        matrix[int(cy)] = row
    return matrix


def _calendar_year_coverage(df: pd.DataFrame) -> dict:
    out: dict[int, dict[str, float | int | str]] = {}
    for year, sub in df.groupby(df["date"].dt.year):
        start = pd.Timestamp(f"{int(year)}-01-01")
        end = pd.Timestamp(f"{int(year)}-12-31")
        expected = len(pd.bdate_range(start, end))
        n_dates = int(sub["date"].nunique())
        coverage = float(n_dates / max(expected, 1))
        out[int(year)] = {
            "n_rows": int(len(sub)),
            "n_dates": n_dates,
            "expected_business_days": expected,
            "coverage": coverage,
            "quality_bucket": _coverage_bucket(coverage),
        }
    return out


def _coverage_bucket(coverage: float) -> str:
    if coverage >= _COVERAGE_OK:
        return "high"
    if coverage >= _COVERAGE_PARTIAL:
        return "medium"
    if coverage > 0:
        return "low"
    return "none"


def _coverage_verdict(matrix: dict) -> dict:
    verdicts: dict = {}
    for cy, row in matrix.items():
        h_cov = row.get("H", 0)
        if h_cov >= _COVERAGE_OK:
            v = "acceptable"
        elif h_cov >= _COVERAGE_PARTIAL:
            v = "partial"
        else:
            v = "insufficient"
        verdicts[cy] = {"H_coverage": h_cov, "verdict": v}
    return verdicts


def _source_labels(df: pd.DataFrame) -> pd.Series:
    def _label(row: pd.Series) -> str:
        source_quality = str(row.get("source_quality", "")).lower()
        source = str(row.get("source", "")).lower()
        is_proxy = bool(row.get("is_proxy", False))
        if "official" in source_quality or "euronext" in source and not is_proxy:
            return "official_recent"
        if "barchart" in source_quality or "barchart" in source:
            return "proxy_barchart"
        if "exploratory" in source_quality or is_proxy:
            return "exploratory_proxy"
        return "unknown"

    return df.apply(_label, axis=1)


def _source_label_counts(df: pd.DataFrame) -> dict:
    labels = _source_labels(df)
    counts = labels.value_counts().to_dict()
    return {str(k): int(v) for k, v in counts.items()}


def _price_outliers(df: pd.DataFrame) -> list[dict]:
    rows = []
    for mc, sub in df.groupby("month_code"):
        price = sub["close_or_last"].dropna()
        if len(price) < 30:
            continue
        z = (price - price.mean()) / price.std()
        flagged = sub.loc[z[z.abs() > 3].index, ["date", "contract_code", "close_or_last"]].copy()
        for _, row in flagged.iterrows():
            rows.append({
                "date": str(pd.Timestamp(row["date"]).date()),
                "contract_code": str(row["contract_code"]),
                "month_code": str(mc),
                "price": float(row["close_or_last"]),
            })
    return rows[:100]


def _data_gaps(front: pd.DataFrame) -> list[dict]:
    if "date" in front.columns:
        dates = pd.to_datetime(front["date"]).sort_values()
    else:
        dates = pd.to_datetime(front.index).sort_values()
    bdays = pd.bdate_range(dates.min(), dates.max())
    missing_bdays = bdays.difference(dates)
    if len(missing_bdays) == 0:
        return []
    gaps = []
    gap_start = missing_bdays[0]
    prev = missing_bdays[0]
    for d in missing_bdays[1:]:
        delta = (d - prev).days
        if delta > 3:
            gaps.append({"start": str(gap_start.date()), "end": str(prev.date()), "n_missing": int((prev - gap_start).days + 1)})
            gap_start = d
        prev = d
    gaps.append({"start": str(gap_start.date()), "end": str(prev.date()), "n_missing": int((prev - gap_start).days + 1)})
    return [g for g in gaps if g["n_missing"] >= 5]


def _oi_stats(df: pd.DataFrame) -> dict:
    oi = df[df["open_interest"].notna() & (df["open_interest"] > 0)]
    stats: dict = {}
    for mc in _MONTH_CODES:
        sub = oi[oi["month_code"] == mc]["open_interest"]
        if len(sub):
            stats[mc] = {
                "mean": float(sub.mean()),
                "max": float(sub.max()),
                "pct_days_oi_positive": float((sub > 0).mean()),
            }
        else:
            stats[mc] = {"mean": 0, "max": 0, "pct_days_oi_positive": 0}
    return stats


def _availability_stats(df: pd.DataFrame) -> dict:
    out: dict[str, float | int] = {"n_rows": int(len(df))}
    for col in ["volume", "open_interest", "settlement", "close_or_last"]:
        if col in df.columns:
            out[f"{col}_non_null_rate"] = float(df[col].notna().mean())
            if col in ["volume", "open_interest"]:
                out[f"{col}_positive_rate"] = float((df[col].fillna(0) > 0).mean())
    return out


def _proxy_vs_official(df: pd.DataFrame) -> dict:
    official = df[df["source_quality"].str.contains("official", case=False, na=False)]
    proxy = df[df["source_quality"].str.contains("exploratory", case=False, na=False)]
    result: dict = {
        "n_official": int(len(official)),
        "n_proxy": int(len(proxy)),
    }
    if len(official) and len(proxy):
        keys = ["date", "canonical_contract_code"]
        aligned = official[keys + ["close_or_last"]].merge(
            proxy[keys + ["close_or_last"]],
            on=keys,
            how="inner",
            suffixes=("_official", "_proxy"),
        ).dropna()
        result["n_overlap_contract_dates"] = int(len(aligned))
        if len(aligned):
            err = aligned["close_or_last_official"] - aligned["close_or_last_proxy"]
            result["mae"] = float(err.abs().mean())
            result["corr"] = float(aligned["close_or_last_official"].corr(aligned["close_or_last_proxy"]))
    else:
        result["verdict"] = "NO_OFFICIAL_DATA — only proxy available"
    return result


def _ml_period_verdict(cov_verdicts: dict) -> str:
    acceptable_years = [cy for cy, v in cov_verdicts.items() if v["verdict"] == "acceptable"]
    if len(acceptable_years) >= 3:
        start = min(acceptable_years)
        end = max(acceptable_years)
        return f"{start}-10-01 to {end + 1}-09-30"
    elif acceptable_years:
        return f"LIMITED — only {len(acceptable_years)} crop year(s) with acceptable coverage"
    return "NO_RELIABLE_PERIOD"


def _periods_from_quality(calendar_cov: dict) -> dict:
    usable = []
    excluded = []
    for year, row in calendar_cov.items():
        entry = {
            "year": int(year),
            "coverage": float(row["coverage"]),
            "quality_bucket": str(row["quality_bucket"]),
        }
        if row["quality_bucket"] in {"high", "medium"}:
            usable.append(entry)
        else:
            excluded.append(entry)
    return {
        "periods_usable_for_research": usable,
        "periods_excluded": excluded,
    }


def _quality_score_by_year(calendar_cov: dict, df: pd.DataFrame) -> dict:
    tmp = pd.DataFrame({"year": df["date"].dt.year, "source_label": _source_labels(df)})
    counts = tmp.groupby(["year", "source_label"]).size().unstack(fill_value=0)

    scores = {}
    for year, row in calendar_cov.items():
        labels_year = counts.loc[int(year)] if int(year) in counts.index else pd.Series(dtype=float)
        n = max(float(labels_year.sum()), 1.0)
        official_share = float(labels_year.get("official_recent", 0) / n)
        proxy_share = float(
            (labels_year.get("proxy_barchart", 0) + labels_year.get("exploratory_proxy", 0)) / n
        )
        score = 0.70 * float(row["coverage"]) + 0.30 * official_share - 0.10 * proxy_share
        scores[int(year)] = {
            "score": float(max(0.0, min(1.0, score))),
            "coverage": float(row["coverage"]),
            "official_share": float(official_share),
            "proxy_share": float(proxy_share),
            "verdict": "research_ok" if score >= 0.60 else "exploratory_only",
        }
    return scores


def build_data_audit_v2() -> dict:
    df = pd.read_parquet(EMA_CONTRACT_DAILY)
    df["date"] = pd.to_datetime(df["date"])

    matrix = _coverage_matrix(df)
    calendar_cov = _calendar_year_coverage(df)
    cov_verdicts = _coverage_verdict(matrix)
    verdict_ml = _ml_period_verdict(cov_verdicts)
    periods = _periods_from_quality(calendar_cov)

    front = pd.read_parquet(EMA_FRONT_RAW) if EMA_FRONT_RAW.exists() else pd.DataFrame()
    gaps = _data_gaps(front) if len(front) else []

    price_dist: dict = {}
    for mc in _MONTH_CODES:
        sub = df[df["month_code"] == mc]["close_or_last"].dropna()
        if len(sub):
            price_dist[mc] = {
                "n": int(len(sub)),
                "mean": float(sub.mean()),
                "min": float(sub.min()),
                "q25": float(sub.quantile(0.25)),
                "median": float(sub.median()),
                "q75": float(sub.quantile(0.75)),
                "max": float(sub.max()),
            }

    active_contracts_per_day: dict = {}
    if len(df):
        active = df.groupby("date")["month_code"].count()
        for k in range(6):
            active_contracts_per_day[str(k)] = int((active == k).sum())
        active_contracts_per_day["2+"] = int((active >= 2).sum())
        total_days = int(len(active))
        active_contracts_per_day["pct_2plus"] = float((active >= 2).sum() / max(total_days, 1))
        active_contracts_per_day["mean"] = float(active.mean())
        active_contracts_per_day["min"] = int(active.min())
        active_contracts_per_day["max"] = int(active.max())

    source_counts = df["source_quality"].value_counts().to_dict()

    return {
        "total_rows": int(len(df)),
        "coverage_matrix": matrix,
        "coverage_by_calendar_year": calendar_cov,
        "coverage_verdicts": cov_verdicts,
        "verdict_period_ml": verdict_ml,
        "gaps": gaps,
        "price_outliers_3sigma": _price_outliers(df),
        "price_dist_by_month_code": price_dist,
        "oi_stats": _oi_stats(df),
        "availability_stats": _availability_stats(df),
        "proxy_vs_official": _proxy_vs_official(df),
        "active_contracts_per_day": active_contracts_per_day,
        "source_quality_counts": {str(k): int(v) for k, v in source_counts.items()},
        "source_label_counts": _source_label_counts(df),
        "data_quality_score_by_year": _quality_score_by_year(calendar_cov, df),
        **periods,
        "source_quality": "exploratoire_barchart_proxy",
        "verdict_data": "NO_RELIABLE_PERIOD_ML",
        "limitations": [
            "Source Barchart proxy exploratoire majoritaire.",
            "Settlement officiel historique absent sur une large partie de l'échantillon.",
            "La courbe EMA est partielle : peu de dates ont plusieurs maturités actives.",
        ],
    }


def save_audit_v2(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_data_audit_v2()

    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return str(obj.date())
        raise TypeError(f"Not serialisable: {type(obj)}")

    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=_convert)
    _write_markdown(data, _DOC_OUTPUT)
    return path


def _write_markdown(data: dict, path: Path) -> None:
    lines = [
        "# EMA DATA AUDIT V2",
        "",
        "> Source EMA exploratoire/proxy. Verdict data : NO_RELIABLE_PERIOD_ML.",
        "",
        "## Verdict",
        "",
        f"- Lignes contrats : {data['total_rows']}",
        f"- Période ML fiable : {data['verdict_period_ml']}",
        f"- Source quality : {data['source_quality']}",
        f"- Dates avec >=2 contrats : {data['active_contracts_per_day'].get('pct_2plus', 0):.1%}",
        f"- Contrats actifs par date : moyenne {data['active_contracts_per_day'].get('mean', 0):.2f}, min {data['active_contracts_per_day'].get('min')}, max {data['active_contracts_per_day'].get('max')}",
        "",
        "## Sources",
        "",
        "| Label | Lignes |",
        "|---|---:|",
    ]
    for label, count in data["source_label_counts"].items():
        lines.append(f"| {label} | {count} |")
    lines += [
        "",
        "## Couverture par année",
        "",
        "| Année | Couverture | Score qualité | Verdict |",
        "|---|---:|---:|---|",
    ]
    scores = data["data_quality_score_by_year"]
    for year, row in data["coverage_by_calendar_year"].items():
        score = scores[str(year)] if str(year) in scores else scores[int(year)]
        lines.append(
            f"| {year} | {row['coverage']:.1%} | {score['score']:.2f} | {score['verdict']} |"
        )
    lines += [
        "",
        "## Périodes utilisables",
        "",
        "Les périodes ci-dessous sont utilisables pour recherche exploratoire, pas pour conclusion production.",
    ]
    for period in data["periods_usable_for_research"]:
        lines.append(f"- {period['year']} : {period['quality_bucket']} ({period['coverage']:.1%})")
    lines += ["", "## Limites", ""]
    for limitation in data["limitations"]:
        lines.append(f"- {limitation}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    out = save_audit_v2()
    print(f"Audit v2 saved → {out}")

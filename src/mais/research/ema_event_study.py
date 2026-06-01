"""NB-EMA-09 — Event study grands mouvements EMA : fenêtres J-10 à J+20."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from mais.paths import ARTEFACTS_DIR, FEATURES_PARQUET

_STUDY_DIR = ARTEFACTS_DIR / "ema_study"
_OUTPUT = _STUDY_DIR / "ema_event_study.json"
_WINDOW_PRE = 10
_WINDOW_POST = 20
_SHOCK_SIGMA = 2.0


def _load_ema_returns(feats: pd.DataFrame) -> pd.Series:
    feats = feats[feats["ema_front_price"].notna()].copy()
    price = feats.set_index("Date")["ema_front_price"].sort_index()
    return price.pct_change().rename("ema_ret")


def _identify_events(ema_ret: pd.Series, sigma: float) -> pd.DataFrame:
    mu = ema_ret.mean()
    std = ema_ret.std()
    z = (ema_ret - mu) / std
    events = z[z.abs() >= sigma].reset_index()
    events.columns = ["Date", "z_score"]
    events["direction"] = np.sign(events["z_score"]).astype(int)
    events["ema_ret"] = ema_ret[events["Date"]].values
    return events.reset_index(drop=True)


def _compute_car(ema_ret: pd.Series, event_dates: list, pre: int, post: int) -> dict:
    """Cumulative Abnormal Return around event dates."""
    dates_idx = pd.Index(ema_ret.index)
    pre_cars: list[list[float]] = []
    post_cars: list[list[float]] = []

    for ed in event_dates:
        try:
            pos = dates_idx.get_loc(ed)
        except KeyError:
            continue
        pre_slice = ema_ret.iloc[max(0, pos - pre):pos].values
        post_slice = ema_ret.iloc[pos + 1:pos + 1 + post].values
        if len(pre_slice) > 0:
            pre_cars.append(pre_slice.tolist())
        if len(post_slice) > 0:
            post_cars.append(post_slice.tolist())

    def _avg_cumret(cars: list[list[float]], length: int) -> list[float]:
        padded = [c + [float("nan")] * (length - len(c)) for c in cars]
        arr = np.array(padded)
        return np.nanmean(arr, axis=0).tolist() if len(padded) > 0 else []

    avg_pre = _avg_cumret(pre_cars, pre)
    avg_post = _avg_cumret(post_cars, post)
    pre_cum = float(np.nansum(avg_pre)) if avg_pre else float("nan")
    post_cum = float(np.nansum(avg_post)) if avg_post else float("nan")

    return {
        "n_events": len(event_dates),
        "avg_pre_cumret": pre_cum,
        "avg_post_cumret": post_cum,
        "avg_daily_pre": [float(x) for x in avg_pre],
        "avg_daily_post": [float(x) for x in avg_post],
    }


def _asymmetry_test(pos_post: float, neg_post: float) -> dict:
    """Test simple d'asymétrie : chocs négatifs vs positifs en aftermath."""
    if np.isnan(pos_post) or np.isnan(neg_post):
        return {"error": "insufficient_data"}
    return {
        "positive_shock_post_cumret": pos_post,
        "negative_shock_post_cumret": neg_post,
        "asymmetry": float(abs(neg_post) - abs(pos_post)),
        "interpretation": "négatif > positif en magnitude" if abs(neg_post) > abs(pos_post) else "positif >= négatif",
    }


def _cbot_context_on_event_days(feats: pd.DataFrame, event_dates: list) -> dict:
    """Contexte CBOT les jours d'événements EMA."""
    feats = feats[feats["ema_front_price"].notna()].copy()
    feats["cbot_ret"] = feats["cbot_eur_t"].pct_change()
    event_mask = feats["Date"].isin(event_dates)
    sub = feats[event_mask]["cbot_ret"].dropna()
    all_cbot = feats["cbot_ret"].dropna()
    if len(sub) == 0:
        return {"error": "no_cbot_on_events"}
    return {
        "mean_cbot_ret_on_event_days": float(sub.mean()),
        "mean_cbot_ret_overall": float(all_cbot.mean()),
        "n_event_days_with_cbot_move_gt_1pct": int((sub.abs() > 0.01).sum()),
    }


def build_event_study() -> dict:
    feats = pd.read_parquet(FEATURES_PARQUET)
    feats["Date"] = pd.to_datetime(feats["Date"])
    feats = feats.sort_values("Date").reset_index(drop=True)

    ema_ret = _load_ema_returns(feats)
    events = _identify_events(ema_ret, _SHOCK_SIGMA)

    pos_events = events[events["direction"] > 0]["Date"].tolist()
    neg_events = events[events["direction"] < 0]["Date"].tolist()
    all_events = events["Date"].tolist()

    car_all = _compute_car(ema_ret, all_events, _WINDOW_PRE, _WINDOW_POST)
    car_pos = _compute_car(ema_ret, pos_events, _WINDOW_PRE, _WINDOW_POST)
    car_neg = _compute_car(ema_ret, neg_events, _WINDOW_PRE, _WINDOW_POST)

    asymmetry = _asymmetry_test(
        car_pos.get("avg_post_cumret", float("nan")),
        car_neg.get("avg_post_cumret", float("nan")),
    )

    cbot_context = _cbot_context_on_event_days(feats, all_events)

    top_events = events.nlargest(5, "z_score")[["Date", "ema_ret", "z_score"]].copy()
    top_events["Date"] = top_events["Date"].astype(str)
    bot_events = events.nsmallest(5, "z_score")[["Date", "ema_ret", "z_score"]].copy()
    bot_events["Date"] = bot_events["Date"].astype(str)

    return {
        "n_events_total": len(events),
        "n_positive": len(pos_events),
        "n_negative": len(neg_events),
        "shock_threshold_sigma": _SHOCK_SIGMA,
        "window_pre_days": _WINDOW_PRE,
        "window_post_days": _WINDOW_POST,
        "car_all_events": car_all,
        "car_positive_events": car_pos,
        "car_negative_events": car_neg,
        "asymmetry_analysis": asymmetry,
        "cbot_context": cbot_context,
        "top5_largest_events": top_events.to_dict(orient="records"),
        "top5_smallest_events": bot_events.to_dict(orient="records"),
        "key_findings": {
            "n_total_events": len(events),
            "post_cumret_all": car_all.get("avg_post_cumret"),
            "post_cumret_positive": car_pos.get("avg_post_cumret"),
            "post_cumret_negative": car_neg.get("avg_post_cumret"),
            "asymmetry_magnitude": asymmetry.get("asymmetry"),
            "mean_reversion_detected": (
                (car_pos.get("avg_post_cumret", 0) or 0) < 0
                and (car_neg.get("avg_post_cumret", 0) or 0) > 0
            ),
        },
    }


def save_event_study(output_path: Path | None = None) -> Path:
    path = output_path or _OUTPUT
    path.parent.mkdir(parents=True, exist_ok=True)
    data = build_event_study()

    def _convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return str(obj.date())
        if isinstance(obj, bool):
            return bool(obj)
        raise TypeError(f"Not serialisable: {type(obj)}")

    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=_convert)
    return path


if __name__ == "__main__":
    out = save_event_study()
    print(f"Event study saved → {out}")

"""Maize Market Direction Indicator.

Aggregates multi-horizon directional probabilities, CQR uncertainty, and SHAP
factor importance into a single BULLISH / BEARISH / NEUTRAL / UNCERTAIN signal.

All thresholds and weights are read from ``config/indicator.yaml`` (V1 formula).

Usage
-----
    from mais.indicator.direction import MaizeDirectionIndicator

    indicator = MaizeDirectionIndicator.load(artefacts_dir)
    signal = indicator.predict()          # latest available date
    signal = indicator.predict("2025-06-01")  # specific date
    print(signal.summary())
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from mais.indicator.persistence import compute_signal_stability_rolling
from mais.paths import ARTEFACTS_DIR
from mais.utils import get_logger

log = get_logger("mais.indicator.direction")

HORIZONS: tuple[int, ...] = (5, 10, 20, 30)
DEFAULT_MODEL = "ridge_factors"

# Fallback constants used when config/indicator.yaml is absent
_DEFAULT_CFG: dict[str, Any] = {
    "signal_rules": {
        "uncertain_confidence_threshold": 0.45,
        "bullish_prob_threshold": 0.60,
        "bearish_prob_threshold": 0.60,
        "min_prob_gap": 0.15,
        "neutral_max_gap": 0.10,
    },
    "confidence_score": {
        "probability_distance_weight": 0.30,
        "model_agreement_weight": 0.25,
        "interval_width_weight": 0.25,
        "signal_stability_weight": 0.20,
        "stability_lookback_days": 3,
        "signal_stability_init": 0.5,
    },
    "confidence": {
        "version": "v4",
        "threshold": 0.35,
        "platt_C": 1.0,
        "signal_stability_window": 5,
        "signal_stability_init": 0.5,
    },
    "consensus": {
        "enabled": True,
        "main_horizon": 20,
        "disagreement_threshold": 0.08,
        "consensus_threshold": 0.55,
        "strong_consensus_threshold": 0.75,
        "strong_confidence_threshold": 0.70,
        "auc_weights": {},
    },
    "horizons": [5, 10, 20, 30],
}

# Historical 75th-percentile of ridge_factors CQR interval width (h5..h30 pooled)
_CQR_WIDTH_P75 = 0.249


def _load_indicator_config() -> dict[str, Any]:
    cfg_path = Path(__file__).parents[3] / "config" / "indicator.yaml"
    if not cfg_path.exists():
        log.warning("indicator_config_missing", path=str(cfg_path))
        return _DEFAULT_CFG
    try:
        import yaml  # optional dep — graceful fallback
        with open(cfg_path) as f:
            loaded = yaml.safe_load(f)
        return loaded if loaded else _DEFAULT_CFG
    except ImportError:
        log.warning("pyyaml_not_installed", fallback="using defaults")
        return _DEFAULT_CFG


@dataclass
class DirectionSignal:
    """Output of ``MaizeDirectionIndicator.predict()``."""

    date: pd.Timestamp
    prob_up: dict[int, float]          # {5: 0.61, 10: 0.58, 20: 0.66, 30: 0.51}
    prob_strong_up: dict[int, float]   # {5: 0.12, 10: 0.15, 20: 0.22, 30: 0.18}
    prob_strong_down: dict[int, float] # {5: 0.10, 10: 0.11, 20: 0.09, 30: 0.11}
    confidence: float                  # [0, 1]
    label: str                         # BULLISH / BEARISH / NEUTRAL / UNCERTAIN
    downside_risk_score: float = float("nan")
    upside_opportunity_score: float = float("nan")
    factors_bullish: list[str] = field(default_factory=list)
    factors_bearish: list[str] = field(default_factory=list)
    model_used: str = DEFAULT_MODEL
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        lines = [
            f"=== Maize Market Direction Indicator — {self.date.date()} ===",
            f"Signal       : {self.label}",
            f"Confidence   : {self.confidence:.2f}",
            "",
            "Directional Probabilities (P up):",
        ]
        for h in HORIZONS:
            bar = _prob_bar(self.prob_up.get(h, float("nan")))
            lines.append(f"  J+{h:<3}  {self.prob_up.get(h, float('nan')):.3f}  {bar}")
        lines += [
            "",
            "Strong-move Probabilities:",
            f"  P(strong up  h20)  : {self.prob_strong_up.get(20, float('nan')):.3f}",
            f"  P(strong down h20) : {self.prob_strong_down.get(20, float('nan')):.3f}",
            f"  P(strong up  h30)  : {self.prob_strong_up.get(30, float('nan')):.3f}",
            f"  P(strong down h30) : {self.prob_strong_down.get(30, float('nan')):.3f}",
            "",
            f"Risk / opportunity   : down={self.downside_risk_score:.3f}, up={self.upside_opportunity_score:.3f}",
        ]
        if self.factors_bullish:
            lines.append("\nTop bullish factors : " + ", ".join(self.factors_bullish))
        if self.factors_bearish:
            lines.append("Top bearish factors : " + ", ".join(self.factors_bearish))
        if self.metadata:
            lines.append(
                f"\n(model={self.model_used}, "
                f"avg_cqr_width={self.metadata.get('avg_interval_width', 'N/A'):.3f})"
            )
        return "\n".join(lines)


class MaizeDirectionIndicator:
    """Maize directional indicator backed by study artefacts.

    All thresholds and confidence-score weights are read from
    ``config/indicator.yaml`` (V1 formula).  Missing keys fall back to
    ``_DEFAULT_CFG`` so the indicator always produces a valid signal.

    Call ``load()`` to instantiate from an artefacts directory produced by
    ``build_professional_study()``.  Then call ``predict()`` to get the
    signal for the latest available date or for a specific date.
    """

    def __init__(
        self,
        calibrated_preds: pd.DataFrame,
        shap_df: pd.DataFrame,
        factors_df: pd.DataFrame | None = None,
        model: str = DEFAULT_MODEL,
        config: dict[str, Any] | None = None,
    ) -> None:
        self._preds = calibrated_preds
        self._shap = shap_df
        self._factors = factors_df
        self.model = model
        self.config = config if config is not None else _load_indicator_config()

        sr = self.config.get("signal_rules", _DEFAULT_CFG["signal_rules"])
        conf_cfg = self.config.get("confidence", _DEFAULT_CFG["confidence"])
        self._uncertain_threshold = float(
            conf_cfg.get("threshold", sr.get("uncertain_confidence_threshold", 0.45))
        )
        self._bullish_threshold = float(sr.get("bullish_prob_threshold", 0.60))
        self._bearish_threshold = float(sr.get("bearish_prob_threshold", 0.60))
        self._min_prob_gap = float(sr.get("min_prob_gap", 0.15))
        self._neutral_max_gap = float(sr.get("neutral_max_gap", 0.10))
        self._confidence_version = str(conf_cfg.get("version", "v4"))
        self._stability_window = int(conf_cfg.get("signal_stability_window", 5))
        self._stability_init = float(conf_cfg.get("signal_stability_init", 0.5))
        consensus_cfg = self.config.get("consensus", _DEFAULT_CFG["consensus"])
        self._consensus_enabled = bool(consensus_cfg.get("enabled", True))
        self._consensus_main_horizon = int(consensus_cfg.get("main_horizon", 20))
        self._consensus_disagreement_threshold = float(
            consensus_cfg.get("disagreement_threshold", 0.08)
        )
        self._consensus_threshold = float(consensus_cfg.get("consensus_threshold", 0.55))
        self._strong_consensus_threshold = float(
            consensus_cfg.get("strong_consensus_threshold", 0.75)
        )
        self._strong_confidence_threshold = float(
            consensus_cfg.get("strong_confidence_threshold", 0.70)
        )
        self._consensus_auc_weights = {
            int(k): float(v) for k, v in consensus_cfg.get("auc_weights", {}).items()
        }

        cs = self.config.get("confidence_score", _DEFAULT_CFG["confidence_score"])
        self._w_prob_distance = float(cs.get("probability_distance_weight", 0.30))
        self._w_model_agreement = float(cs.get("model_agreement_weight", 0.25))
        self._w_interval_width = float(cs.get("interval_width_weight", 0.25))
        self._w_signal_stability = float(cs.get("signal_stability_weight", 0.20))
        self._stability_init = float(cs.get("signal_stability_init", self._stability_init))

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def load(
        cls,
        artefacts_dir: Path | str | None = None,
        model: str = DEFAULT_MODEL,
        config: dict[str, Any] | None = None,
    ) -> MaizeDirectionIndicator:
        """Load indicator from artefacts produced by the study pipeline."""
        base = Path(artefacts_dir) if artefacts_dir else Path(ARTEFACTS_DIR) / "professional_study"

        calib_path = base / "calibrated_predictions.parquet"
        shap_path = base / "shap_importance.parquet"

        if not calib_path.exists():
            raise FileNotFoundError(
                f"calibrated_predictions.parquet not found at {base}. "
                "Run `make study` first."
            )

        calibrated_preds = pd.read_parquet(calib_path)
        shap_df = pd.read_parquet(shap_path) if shap_path.exists() else pd.DataFrame()

        factors_path = Path("data/processed/factors.parquet")
        factors_df: pd.DataFrame | None = None
        if factors_path.exists():
            try:
                factors_df = pd.read_parquet(factors_path)
                factors_df["Date"] = pd.to_datetime(factors_df["Date"])
            except Exception:
                pass

        loaded_config = config if config is not None else _load_indicator_config()
        log.info(
            "indicator_loaded",
            model=model,
            n_calib_rows=len(calibrated_preds),
            has_shap=not shap_df.empty,
            has_factors=factors_df is not None,
        )
        return cls(
            calibrated_preds=calibrated_preds,
            shap_df=shap_df,
            factors_df=factors_df,
            model=model,
            config=loaded_config,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, date: str | pd.Timestamp | None = None) -> DirectionSignal:
        """Return a DirectionSignal for *date* (default: latest available date)."""
        preds_model = self._preds[self._preds["model"] == self.model].copy()
        if preds_model.empty:
            raise ValueError(
                f"No predictions found for model '{self.model}' in calibrated_predictions."
            )

        preds_model["Date"] = pd.to_datetime(preds_model["Date"])

        target_date = preds_model["Date"].max() if date is None else pd.to_datetime(date)

        prob_up: dict[int, float] = {}
        prob_strong_up: dict[int, float] = {}
        prob_strong_down: dict[int, float] = {}
        interval_widths: list[float] = []
        row_per_horizon: dict[int, pd.Series] = {}

        for h in HORIZONS:
            horizon_preds = preds_model[
                (preds_model["horizon"] == h) & (preds_model["Date"] <= target_date)
            ]
            if horizon_preds.empty:
                continue
            r = horizon_preds.sort_values("Date").iloc[-1]
            row_per_horizon[h] = r
            p_up_col = f"p_up_h{h}"
            if p_up_col in r.index and pd.notna(r[p_up_col]):
                prob_up[h] = float(r[p_up_col])
            if f"p_up_strong_h{h}" in r.index and pd.notna(r[f"p_up_strong_h{h}"]):
                prob_strong_up[h] = float(r[f"p_up_strong_h{h}"])
            if f"p_down_strong_h{h}" in r.index and pd.notna(r[f"p_down_strong_h{h}"]):
                prob_strong_down[h] = float(r[f"p_down_strong_h{h}"])
            if "interval_width_logret_90" in r.index and pd.notna(r["interval_width_logret_90"]):
                interval_widths.append(float(r["interval_width_logret_90"]))

        if not prob_up:
            raise ValueError(f"No prob_up values found for date {target_date.date()}.")

        self._fill_missing_prob_up(row_per_horizon, prob_up, prob_strong_up, prob_strong_down)

        avg_width = float(np.mean(interval_widths)) if interval_widths else _CQR_WIDTH_P75
        signal_stability = self._estimate_signal_stability(preds_model, target_date)
        if self._confidence_version == "v4":
            confidence = self._compute_confidence_v4(
                auc_contexte=0.655,
                accord_modeles=self._cross_horizon_agreement(prob_up),
                prob_up_raw=float(np.mean(list(prob_up.values()))),
                cqr_width_norm=min(1.0, avg_width / _CQR_WIDTH_P75),
                signal_stability=signal_stability,
            )
        else:
            confidence = self._compute_confidence(prob_up, avg_width, signal_stability)
        consensus_result = None
        if self._consensus_enabled:
            from mais.indicator.consensus import compute_consensus_score

            auc_weights = {
                h: self._consensus_auc_weights.get(h, 0.655)
                for h in prob_up
            }
            consensus_result = compute_consensus_score(
                prob_up,
                auc_weights=auc_weights,
                main_horizon=self._consensus_main_horizon,
            )
        label = self._label(prob_up, confidence, consensus_result=consensus_result)

        factors_bull, factors_bear = self._factor_attribution(target_date, prob_up, label)
        signal_force = self._signal_force(confidence, consensus_result)
        downside_risk_score, upside_opportunity_score = self._asymmetric_scores(
            prob_up,
            prob_strong_up,
            prob_strong_down,
        )

        return DirectionSignal(
            date=target_date,
            prob_up=prob_up,
            prob_strong_up=prob_strong_up,
            prob_strong_down=prob_strong_down,
            confidence=confidence,
            label=label,
            downside_risk_score=downside_risk_score,
            upside_opportunity_score=upside_opportunity_score,
            factors_bullish=factors_bull,
            factors_bearish=factors_bear,
            model_used=self.model,
            metadata={
                "avg_interval_width": avg_width,
                "signal_stability": signal_stability,
                "confidence_version": self._confidence_version,
                "signal_force": signal_force,
                "consensus_score": (
                    None if consensus_result is None else consensus_result["consensus_score"]
                ),
                "consensus_disagreement": (
                    None if consensus_result is None else consensus_result["disagreement"]
                ),
                "consensus_direction": (
                    None if consensus_result is None else consensus_result["consensus_direction"]
                ),
                "downside_risk_score": downside_risk_score,
                "upside_opportunity_score": upside_opportunity_score,
            },
        )

    def predict_range(
        self, start: str, end: str, freq: str = "B"
    ) -> pd.DataFrame:
        """Return a DataFrame of signals for every business day in [start, end]."""
        preds_model = self._preds[self._preds["model"] == self.model].copy()
        preds_model["Date"] = pd.to_datetime(preds_model["Date"])
        available_dates = sorted(preds_model["Date"].unique())

        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end)
        dates = [d for d in available_dates if start_ts <= d <= end_ts]

        records = []
        for d in dates:
            try:
                sig = self.predict(d)
            except ValueError:
                continue
            row = {
                "Date": sig.date,
                "label": sig.label,
                "confidence": sig.confidence,
                "downside_risk_score": sig.downside_risk_score,
                "upside_opportunity_score": sig.upside_opportunity_score,
            }
            for h in HORIZONS:
                row[f"prob_up_h{h}"] = sig.prob_up.get(h, float("nan"))
            records.append(row)

        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fill_missing_prob_up(
        self,
        row_per_horizon: dict[int, pd.Series],
        prob_up: dict[int, float],
        prob_strong_up: dict[int, float],
        prob_strong_down: dict[int, float],
    ) -> None:
        """Fill missing horizon probs from logret midpoint via logistic transform."""
        for h in HORIZONS:
            if h in prob_up:
                continue
            r = row_per_horizon.get(h)
            if r is None:
                continue
            if "q50_logret" in r.index and pd.notna(r["q50_logret"]):
                midpoint = float(r["q50_logret"])
                vol_scale = 0.036 * (h / 5) ** 0.5
                prob_up[h] = float(1.0 / (1.0 + np.exp(-midpoint / vol_scale)))
            if h not in prob_strong_up and "q90_logret" in r.index and pd.notna(r["q90_logret"]):
                prob_strong_up[h] = max(0.0, float(r["q90_logret"]) / 0.10)
            if h not in prob_strong_down and "q10_logret" in r.index and pd.notna(r["q10_logret"]):
                prob_strong_down[h] = max(0.0, -float(r["q10_logret"]) / 0.10)

    @staticmethod
    def _historical_context_confidence(
        season: str,
        regime: str,
        vol_bucket: str,
        lookback_df: pd.DataFrame,
        min_obs: int = 50,
    ) -> float:
        """Fraction of past similar-context days where the direction was correct.

        Requires a lookback_df with columns: season, regime, vol_bucket, correct.
        Returns 0.5 (neutral) when n_obs < min_obs (50 — per project guard-fous).
        """
        if lookback_df is None or lookback_df.empty:
            return 0.5
        mask = (
            (lookback_df["season"] == season)
            & (lookback_df["regime"] == regime)
            & (lookback_df["vol_bucket"] == vol_bucket)
        )
        similar = lookback_df[mask]
        if len(similar) < min_obs:
            return 0.5
        da_hist = float(similar["correct"].mean())
        # Normalise: 0.5 DA → 0.0 confidence, 0.8 DA → 1.0 confidence
        return float(np.clip((da_hist - 0.5) / 0.30, 0.0, 1.0))

    def _compute_confidence_components(
        self, prob_up: dict[int, float], avg_width: float, signal_stability: float | None = None
    ) -> tuple[float, float, float, float]:
        """Return (prob_distance, model_agreement, interval_width, stability) ∈ [0,1]."""
        values = [v for v in prob_up.values() if np.isfinite(v)]
        if not values:
            return 0.0, 0.0, 0.0, 0.0

        mean_p = float(np.mean(values))
        prob_distance = min(1.0, abs(mean_p - 0.5) * 2)
        std_p = float(np.std(values)) if len(values) > 1 else 0.0
        model_agreement = max(0.0, 1.0 - std_p / 0.15)
        interval_width = max(0.0, 1.0 - avg_width / _CQR_WIDTH_P75)
        st_input = self._stability_init if signal_stability is None else signal_stability
        stability = float(np.clip(st_input, 0.0, 1.0))
        return prob_distance, model_agreement, interval_width, stability

    def _compute_confidence(
        self, prob_up: dict[int, float], avg_width: float, signal_stability: float | None = None
    ) -> float:
        """Confidence score V1 — weighted composite per config/indicator.yaml.

        Components (all normalized to [0, 1]):
          probability_distance : abs(mean_p - 0.5) * 2
          model_agreement      : 1 - normalized cross-horizon std (proxy)
          interval_width       : 1 - normalized CQR width
          signal_stability     : % of last N days with same signal (0.5 if no history)
        """
        values = [v for v in prob_up.values() if np.isfinite(v)]
        if not values:
            return 0.0
        pd_, ma, iw, st = self._compute_confidence_components(
            prob_up, avg_width, signal_stability
        )
        confidence = (
            self._w_prob_distance * pd_
            + self._w_model_agreement * ma
            + self._w_interval_width * iw
            + self._w_signal_stability * st
        )
        return float(np.clip(confidence, 0.0, 1.0))

    def _compute_confidence_v2(
        self,
        prob_up: dict[int, float],
        avg_width: float,
        signal_stability: float | None = None,
        season: str = "unknown",
        regime: str = "bull",
        vol_bucket: str = "normal",
        lookback_df: pd.DataFrame | None = None,
    ) -> float:
        """Confidence score V2 — V1 + historical context component.

        Weights: prob_distance=0.25, model_agreement=0.20,
                 interval_width=0.20, stability=0.15, hist_context=0.20.
        """
        values = [v for v in prob_up.values() if np.isfinite(v)]
        if not values:
            return 0.0
        pd_, ma, iw, st = self._compute_confidence_components(
            prob_up, avg_width, signal_stability
        )
        hist_ctx = self._historical_context_confidence(
            season, regime, vol_bucket, lookback_df if lookback_df is not None else pd.DataFrame()
        )
        confidence = (
            0.25 * pd_
            + 0.20 * ma
            + 0.20 * iw
            + 0.15 * st
            + 0.20 * hist_ctx
        )
        return float(np.clip(confidence, 0.0, 1.0))

    def _compute_confidence_v3(
        self,
        prob_up: dict[int, float],
        avg_width: float,
        signal_stability: float | None = None,
        season: str = "unknown",
        regime: str = "bull",
        vol_bucket: str = "normal",
        lookback_df: pd.DataFrame | None = None,
    ) -> float:
        """Confidence score V3 — conservative: minimum of all components.

        Penalises heavily any weak component. A single low component → low confidence.
        """
        values = [v for v in prob_up.values() if np.isfinite(v)]
        if not values:
            return 0.0
        pd_, ma, iw, st = self._compute_confidence_components(
            prob_up, avg_width, signal_stability
        )
        hist_ctx = self._historical_context_confidence(
            season, regime, vol_bucket, lookback_df if lookback_df is not None else pd.DataFrame()
        )
        return float(min(pd_, ma, iw, hist_ctx))

    @staticmethod
    def _compute_confidence_v4(
        auc_contexte: float,
        accord_modeles: float,
        prob_up_raw: float,
        cqr_width_norm: float,
        signal_stability: float,
    ) -> float:
        """Confidence V4 independent from Platt-compressed probabilities."""
        auc_score = float(np.clip((auc_contexte - 0.5) / 0.25, 0.0, 1.0))
        return float(
            np.clip(
                0.25 * auc_score
                + 0.25 * np.clip(accord_modeles, 0.0, 1.0)
                + 0.20 * abs(prob_up_raw - 0.5) * 2.0
                + 0.15 * (1.0 - np.clip(cqr_width_norm, 0.0, 1.0))
                + 0.15 * np.clip(signal_stability, 0.0, 1.0),
                0.0,
                1.0,
            )
        )

    @staticmethod
    def _cross_horizon_agreement(prob_up: dict[int, float]) -> float:
        """Share of available horizons agreeing with the majority direction."""
        values = [v for v in prob_up.values() if np.isfinite(v)]
        if not values:
            return 0.5
        directions = np.array([1 if p > 0.5 else -1 if p < 0.5 else 0 for p in values])
        bullish = int((directions > 0).sum())
        bearish = int((directions < 0).sum())
        neutral = int((directions == 0).sum())
        return max(bullish, bearish, neutral) / len(directions)

    def _estimate_signal_stability(self, preds_model: pd.DataFrame, target_date: pd.Timestamp) -> float:
        """Estimate rolling signal stability from past cross-horizon probabilities."""
        rows: list[dict[str, Any]] = []
        for h in HORIZONS:
            p_col = f"p_up_h{h}"
            if p_col not in preds_model.columns:
                continue
            h_df = preds_model[
                (preds_model["horizon"] == h)
                & (preds_model["Date"] <= target_date)
                & preds_model[p_col].notna()
            ][["Date", p_col]]
            rows.extend({"Date": r.Date, "p": float(getattr(r, p_col))} for r in h_df.itertuples())

        if not rows:
            return self._stability_init

        hist = pd.DataFrame(rows).groupby("Date", as_index=False)["p"].mean().sort_values("Date")
        gap = (hist["p"] - 0.5).abs() * 2.0
        hist["signal"] = "NEUTRAL"
        hist.loc[(hist["p"] > self._bullish_threshold) & (gap > self._min_prob_gap), "signal"] = "BULLISH"
        hist.loc[
            (hist["p"] < (1.0 - self._bearish_threshold)) & (gap > self._min_prob_gap),
            "signal",
        ] = "BEARISH"
        stability = compute_signal_stability_rolling(
            hist["signal"],
            window=self._stability_window,
            initial_value=self._stability_init,
        )
        return float(stability.iloc[-1]) if not stability.empty else self._stability_init

    def _label(
        self,
        prob_up: dict[int, float],
        confidence: float,
        consensus_result: dict[str, Any] | None = None,
    ) -> str:
        """Classify signal — strict order from config/indicator.yaml signal_rules.

        Order (first match wins):
          1. multi-horizon disagreement above threshold -> UNCERTAIN
          2. confidence < uncertain_confidence_threshold -> UNCERTAIN
          3. P(up) > bullish_prob_threshold AND gap > min_prob_gap -> BULLISH
          4. P(up) < (1 - bearish_prob_threshold) AND gap > min_prob_gap -> BEARISH
          5. gap < neutral_max_gap -> NEUTRAL
          6. -> UNCERTAIN (gap between neutral and directional thresholds)
        """
        values = [v for v in prob_up.values() if np.isfinite(v)]
        if not values:
            return "UNCERTAIN"
        if (
            consensus_result is not None
            and float(consensus_result.get("disagreement", 0.0))
            > self._consensus_disagreement_threshold
        ):
            return "UNCERTAIN"

        mean_p = float(np.mean(values))
        # gap = |P(up) - P(down)| = |2*P(up) - 1|
        gap = abs(2.0 * mean_p - 1.0)

        if confidence < self._uncertain_threshold:
            return "UNCERTAIN"
        if mean_p > self._bullish_threshold and gap > self._min_prob_gap:
            return "BULLISH"
        if mean_p < (1.0 - self._bearish_threshold) and gap > self._min_prob_gap:
            return "BEARISH"
        if gap < self._neutral_max_gap:
            return "NEUTRAL"
        return "UNCERTAIN"

    def _signal_force(self, confidence: float, consensus_result: dict[str, Any] | None) -> str:
        """Return weak, medium or strong for downstream presentation."""
        if consensus_result is None:
            return "medium"
        score = float(consensus_result.get("consensus_score", 0.0))
        if score < self._consensus_threshold:
            return "weak"
        if score > self._strong_consensus_threshold and confidence > self._strong_confidence_threshold:
            return "strong"
        return "medium"

    @staticmethod
    def _asymmetric_scores(
        prob_up: dict[int, float],
        prob_strong_up: dict[int, float],
        prob_strong_down: dict[int, float],
    ) -> tuple[float, float]:
        """Return downside risk and upside opportunity scores for presentation."""
        down_values = [float(v) for v in prob_strong_down.values() if np.isfinite(v)]
        up_values = [float(v) for v in prob_strong_up.values() if np.isfinite(v)]
        if down_values:
            downside = float(np.clip(np.mean(down_values), 0.0, 1.0))
        else:
            p_mean = float(np.mean([v for v in prob_up.values() if np.isfinite(v)]))
            downside = float(np.clip((0.5 - p_mean) * 2.0, 0.0, 1.0))
        if up_values:
            upside = float(np.clip(np.mean(up_values), 0.0, 1.0))
        else:
            p_mean = float(np.mean([v for v in prob_up.values() if np.isfinite(v)]))
            upside = float(np.clip((p_mean - 0.5) * 2.0, 0.0, 1.0))
        return downside, upside

    def _factor_attribution(
        self,
        date: pd.Timestamp,
        prob_up: dict[int, float],
        label: str,
    ) -> tuple[list[str], list[str]]:
        """Return top bullish and bearish factors from SHAP + factor values."""
        if self._shap.empty:
            return [], []

        dominant_horizon = max(prob_up, key=lambda h: abs(prob_up[h] - 0.5))

        shap_h = self._shap[self._shap["horizon"] == dominant_horizon].copy()
        if shap_h.empty:
            shap_h = self._shap.copy()

        shap_top = shap_h.nlargest(10, "abs_coef")

        factor_signs: dict[str, float] = {}
        if self._factors is not None:
            dates_avail = self._factors["Date"].values
            idx = np.argmin(np.abs(dates_avail - np.datetime64(date)))
            if len(dates_avail) > 0:
                frow = self._factors.iloc[idx]
                for f in shap_top["factor"].tolist():
                    if f in frow.index and pd.notna(frow[f]):
                        factor_signs[f] = float(frow[f])

        try:
            from mais.features.factors import get_factor_metadata
            meta = get_factor_metadata()
            meta_dict = dict(zip(meta["factor_name"], meta.get("expected_sign", pd.Series([])), strict=False))
        except Exception:
            meta_dict = {}

        factors_bull: list[str] = []
        factors_bear: list[str] = []

        for _, row in shap_top.iterrows():
            fname = str(row["factor"])
            fval = factor_signs.get(fname, 0.0)
            expected = meta_dict.get(fname, "positive")

            is_bullish = fval < 0 if expected == "negative" else fval > 0

            if is_bullish:
                factors_bull.append(fname)
            else:
                factors_bear.append(fname)

        if label == "BEARISH":
            factors_bull, factors_bear = factors_bear, factors_bull

        return factors_bull[:3], factors_bear[:3]


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def build_indicator(
    artefacts_dir: Path | str | None = None,
    model: str = DEFAULT_MODEL,
) -> MaizeDirectionIndicator:
    """Convenience wrapper around ``MaizeDirectionIndicator.load()``."""
    return MaizeDirectionIndicator.load(artefacts_dir=artefacts_dir, model=model)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _prob_bar(p: float, width: int = 20) -> str:
    """ASCII bar for a probability in [0, 1]."""
    if not np.isfinite(p):
        return "[" + "?" * width + "]"
    filled = int(round(p * width))
    return "[" + "█" * filled + "░" * (width - filled) + "]"

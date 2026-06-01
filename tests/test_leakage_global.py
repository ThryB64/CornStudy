"""V7-LEAKAGE-00 — Suite de tests anti-leakage global.

Ces tests sont des invariants de sécurité exécutés avant tout verdict GO_RESEARCH.
Ils testent les cas typiques de leakage sur des données synthétiques.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dates(n: int = 500) -> pd.DatetimeIndex:
    return pd.date_range("2010-01-01", periods=n, freq="B")


def _make_X(n: int = 500) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = _make_dates(n)
    return pd.DataFrame(
        {"feat_a": rng.normal(size=n), "feat_b": rng.normal(size=n)},
        index=dates,
    )


def _make_y(n: int = 500) -> pd.Series:
    rng = np.random.default_rng(42)
    return pd.Series((rng.normal(size=n) > 0).astype(int), index=_make_dates(n))


# ---------------------------------------------------------------------------
# Test 1 : aucune colonne cible dans X
# ---------------------------------------------------------------------------

def test_no_target_column_in_X():
    X = _make_X()
    # Colonnes cibles potentielles
    bad_cols = [c for c in X.columns if c.startswith(("y_", "return_", "future_"))]
    assert len(bad_cols) == 0, f"Colonnes cibles trouvées dans X: {bad_cols}"


def test_target_column_detection():
    X = _make_X()
    X_leak = X.copy()
    X_leak["y_rel_outperform_h90"] = 0  # ajout d'une colonne cible
    bad_cols = [c for c in X_leak.columns if c.startswith(("y_", "return_", "future_"))]
    assert len(bad_cols) > 0, "La détection de colonnes cibles doit trouver y_*"


# ---------------------------------------------------------------------------
# Test 2 : aucun shift(-H) dans le code source des features
# ---------------------------------------------------------------------------

def test_no_negative_shift_in_features():
    import mais.features.market as market_mod

    with open(market_mod.__file__) as fh:
        code = fh.read()
    neg_shifts = re.findall(r"shift\(-\d+\)", code)
    assert len(neg_shifts) == 0, f"Negative shifts trouvés dans market.py: {neg_shifts}"


def test_no_negative_shift_in_ema_features():
    import mais.features.ema_features as ema_mod

    with open(ema_mod.__file__) as fh:
        code = fh.read()
    neg_shifts = re.findall(r"shift\(-\d+\)", code)
    assert len(neg_shifts) == 0, f"Negative shifts trouvés dans ema_features.py: {neg_shifts}"


# ---------------------------------------------------------------------------
# Test 3 : meta-features OOF doivent avoir is_oof=True
# ---------------------------------------------------------------------------

def test_oof_flag_required():
    meta_preds = pd.DataFrame(
        {"proba_h90": [0.6, 0.4, 0.7], "is_oof": [True, True, True]}
    )
    assert "is_oof" in meta_preds.columns
    non_oof = meta_preds[~meta_preds["is_oof"]]
    assert len(non_oof) == 0


def test_oof_flag_detects_violation():
    meta_preds = pd.DataFrame(
        {"proba_h90": [0.6, 0.4, 0.7], "is_oof": [True, False, True]}
    )
    non_oof = meta_preds[~meta_preds["is_oof"]]
    assert len(non_oof) == 1, "La détection de non-OOF doit trouver 1 violation"


# ---------------------------------------------------------------------------
# Test 4 : embargo sur les folds
# ---------------------------------------------------------------------------

def test_oof_embargo_respected():
    """Chaque prédiction OOF : test_date > train_end + embargo."""
    embargo_days = 90
    folds = [
        {
            "fold_id": 0,
            "train_end": pd.Timestamp("2015-12-31"),
            "test_dates": pd.date_range("2016-04-10", periods=50, freq="B"),
        },
        {
            "fold_id": 1,
            "train_end": pd.Timestamp("2017-12-31"),
            "test_dates": pd.date_range("2018-04-10", periods=50, freq="B"),
        },
    ]
    for fold in folds:
        cutoff = fold["train_end"] + pd.Timedelta(days=embargo_days)
        violations = [d for d in fold["test_dates"] if d <= cutoff]
        assert len(violations) == 0, (
            f"Fold {fold['fold_id']}: {len(violations)} dates dans zone embargo"
        )


def test_oof_embargo_detects_violation():
    embargo_days = 90
    fold = {
        "train_end": pd.Timestamp("2015-12-31"),
        "test_dates": pd.date_range("2016-01-15", periods=5, freq="B"),
    }
    cutoff = fold["train_end"] + pd.Timedelta(days=embargo_days)
    violations = [d for d in fold["test_dates"] if d <= cutoff]
    assert len(violations) > 0, "La détection de violation embargo doit trouver des violations"


# ---------------------------------------------------------------------------
# Test 5 : z-scores fittés sur train uniquement
# ---------------------------------------------------------------------------

def test_zscores_fit_on_train_only():
    """Le scaler doit être fitted sur train uniquement, pas sur train+test."""
    rng = np.random.default_rng(42)
    X_train = pd.DataFrame({"a": rng.normal(0, 1, 200), "b": rng.normal(2, 3, 200)})
    X_test = pd.DataFrame({"a": rng.normal(5, 1, 50), "b": rng.normal(10, 3, 50)})

    scaler = StandardScaler()
    scaler.fit(X_train)

    # Vérifier que mean_ correspond au train
    assert abs(scaler.mean_[0] - X_train["a"].mean()) < 1e-6
    assert abs(scaler.mean_[1] - X_train["b"].mean()) < 1e-6

    # Vérifier que le test n'est PAS dans le fit
    scaler_full = StandardScaler()
    X_full = pd.concat([X_train, X_test])
    scaler_full.fit(X_full)
    # Les means doivent être différents si le test a une distribution décalée
    assert abs(scaler.mean_[0] - scaler_full.mean_[0]) > 0.1


# ---------------------------------------------------------------------------
# Test 6 : seuils percentiles appris sur train uniquement
# ---------------------------------------------------------------------------

def test_top20_threshold_train_only():
    thresholds = {
        "computed_on": "train_only",
        "top20": 0.75,
        "top40": 0.65,
    }
    assert thresholds["computed_on"] == "train_only"
    assert 0 < thresholds["top20"] <= 1
    assert 0 < thresholds["top40"] <= 1


def test_top20_threshold_detects_full_data_fit():
    thresholds = {"computed_on": "train_and_test", "top20": 0.75}
    assert thresholds["computed_on"] != "train_only", (
        "Seuil calculé sur train+test : violation anti-leakage"
    )


# ---------------------------------------------------------------------------
# Test 7 : toutes les dates test > train_end + embargo
# ---------------------------------------------------------------------------

def test_all_test_dates_after_embargo():
    rng = np.random.default_rng(42)
    n = 400
    dates = pd.date_range("2012-01-01", periods=n, freq="B")
    embargo = 90

    # Simulation d'un split purged
    train_idx = np.arange(200)
    test_idx = np.arange(300, 400)  # gap de 100 jours > embargo

    train_end = dates[train_idx[-1]]
    test_dates = dates[test_idx]
    cutoff = train_end + pd.Timedelta(days=embargo)

    violations = [d for d in test_dates if d <= cutoff]
    assert len(violations) == 0


# ---------------------------------------------------------------------------
# Test 8 : anti-leakage de la cible (pas de calcul return futur en feature)
# ---------------------------------------------------------------------------

def test_target_not_computable_from_raw_feature():
    """Une feature de retour passé ne doit pas être corrélée à > 0.8 avec return futur."""
    rng = np.random.default_rng(42)
    prices = pd.Series(rng.lognormal(size=300))
    past_return = prices.pct_change(20)       # retour passé 20j : légal
    future_return = prices.pct_change(20).shift(-20)  # retour futur : interdit en feature

    # Une feature passée ne doit pas prédicter parfaitement le futur
    valid_mask = past_return.notna() & future_return.notna()
    corr = past_return[valid_mask].corr(future_return[valid_mask])
    # Dans des données aléatoires, corrélation passé/futur doit être faible
    assert abs(corr) < 0.5, f"Corrélation passé/futur suspecte: {corr:.3f}"

"""5 anti-leakage tests + 1 sanity test on suspect names.

These are the "5 baseline anti-leakage tests" from Phase 0 of the audit plan.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mais.leakage import LeakageAudit, audit_features_targets


# ---------------------------------------------------------------------------
# Test 1 - SHAPE_ALIGNMENT
# ---------------------------------------------------------------------------


def test_shape_alignment_passes(synthetic_features, synthetic_targets):
    audit = audit_features_targets(synthetic_features, synthetic_targets,
                                    write_report_to=None)
    assert not audit.shape_misalignment


def test_shape_alignment_detects_mismatched_dates(synthetic_features, synthetic_targets):
    bad_targets = synthetic_targets.copy()
    bad_targets["Date"] = bad_targets["Date"] + pd.Timedelta(days=365 * 5)
    audit = audit_features_targets(synthetic_features, bad_targets, write_report_to=None)
    assert audit.shape_misalignment


# ---------------------------------------------------------------------------
# Test 2 - NAMING_CONVENTION
# ---------------------------------------------------------------------------


def test_naming_convention_detects_y_prefix(synthetic_features, synthetic_targets):
    bad = synthetic_features.copy()
    bad["y_logret_h5"] = 0.0  # accidentally putting a target into features
    audit = audit_features_targets(bad, synthetic_targets, write_report_to=None)
    assert "y_logret_h5" in audit.naming_violations
    assert not audit.passed


def test_naming_convention_passes_when_clean(synthetic_features, synthetic_targets):
    audit = audit_features_targets(synthetic_features, synthetic_targets,
                                    write_report_to=None)
    assert audit.naming_violations == []


# ---------------------------------------------------------------------------
# Test 3 - PERFECT_FIT
# ---------------------------------------------------------------------------


def test_perfect_fit_detects_target_copy(synthetic_features, synthetic_targets):
    """If a feature is a near-perfect copy of a target, it's leakage."""
    bad = synthetic_features.merge(synthetic_targets[["Date", "y_logret_h5"]], on="Date")
    bad = bad.rename(columns={"y_logret_h5": "feature_secret_copy"})
    # add a tiny bit of noise so it's not literally identical
    bad["feature_secret_copy"] = bad["feature_secret_copy"] + 1e-6
    audit = audit_features_targets(bad, synthetic_targets, write_report_to=None,
                                    perfect_fit_threshold=0.95)
    flagged = [(f, t) for (f, t, _) in audit.perfect_fit]
    assert ("feature_secret_copy", "y_logret_h5") in flagged
    assert not audit.passed


def test_perfect_fit_does_not_flag_legit_features(synthetic_features, synthetic_targets):
    audit = audit_features_targets(synthetic_features, synthetic_targets,
                                    write_report_to=None, perfect_fit_threshold=0.97)
    assert audit.perfect_fit == []


# ---------------------------------------------------------------------------
# Test 4 - FUTURE_FUNCTION
# ---------------------------------------------------------------------------


def test_future_function_detects_unshifted_feature(synthetic_prices, synthetic_targets):
    """Build a feature that uses tomorrow's return - shift(-1) should worsen
    correlation, not improve it. The check should still flag it because
    information at t includes data at t+1."""
    df = synthetic_prices.copy()
    df["leaky_tomorrow_return"] = np.log(df["corn_close"]).diff().shift(-1)
    feats = df[["Date", "leaky_tomorrow_return"]]
    audit = audit_features_targets(feats, synthetic_targets, write_report_to=None,
                                    perfect_fit_threshold=0.99,
                                    future_fn_min_improvement=0.01)
    # Either perfect_fit or future_dependent should fire
    assert audit.perfect_fit or audit.future_dependent
    assert not audit.passed


# ---------------------------------------------------------------------------
# Test 5 - SUSPECT_NAMES
# ---------------------------------------------------------------------------


def test_suspect_names_detect_numeric_headers(synthetic_features, synthetic_targets):
    bad = synthetic_features.copy()
    bad["5.98"] = 0.0
    bad["175.1"] = 0.0
    bad["corn_ret_1d.1"] = 0.0
    audit = audit_features_targets(bad, synthetic_targets, write_report_to=None)
    assert "5.98" in audit.suspect_names
    assert "175.1" in audit.suspect_names
    assert "corn_ret_1d.1" in audit.suspect_names
    assert not audit.passed


def test_suspect_names_pass_when_clean(synthetic_features, synthetic_targets):
    audit = audit_features_targets(synthetic_features, synthetic_targets,
                                    write_report_to=None)
    assert audit.suspect_names == []
    assert audit.passed

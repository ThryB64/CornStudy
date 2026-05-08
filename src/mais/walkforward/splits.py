"""Walk-forward splits with embargo + purge for horizon-dependent targets.

KEY DIFFERENCE vs the legacy ``yearly_rolling`` strategy: we support a
shorter ``step_days`` (e.g. 21 for monthly retrains) and we EMBARGO the
horizon, which is mandatory when targets are H-step-ahead returns.

Without embargo, the train set up to date T contains targets that look
ahead up to T+H, contaminating the test set that starts at T+1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator

import numpy as np
import pandas as pd


@dataclass
class WalkForwardSplit:
    train_idx: np.ndarray
    test_idx: np.ndarray
    train_end_date: pd.Timestamp
    test_start_date: pd.Timestamp
    test_end_date: pd.Timestamp


@dataclass
class WalkForwardSplitter:
    initial_train_size: int           # number of rows in the first train window
    step_days: int = 21               # how often we re-train
    test_size_days: int = 21          # length of each OOS window
    embargo_days: int = 30            # purge: ignored rows around train/test boundary
    horizon_days: int = 0             # forecast horizon (used to amplify embargo)

    def split(self, dates: pd.Series) -> Iterator[WalkForwardSplit]:
        d = pd.to_datetime(dates).reset_index(drop=True)
        n = len(d)
        embargo = max(self.embargo_days, self.horizon_days)
        train_end = self.initial_train_size - 1
        while train_end < n - 1:
            test_start = train_end + 1 + embargo
            test_end = min(test_start + self.test_size_days - 1, n - 1)
            if test_start >= n:
                break
            train_idx = np.arange(0, train_end + 1)
            test_idx = np.arange(test_start, test_end + 1)
            yield WalkForwardSplit(
                train_idx=train_idx,
                test_idx=test_idx,
                train_end_date=d.iloc[train_end],
                test_start_date=d.iloc[test_start],
                test_end_date=d.iloc[test_end],
            )
            train_end += self.step_days


def generate_walk_forward_splits(
    dates: Iterable, initial_train_years: int = 8, step_days: int = 21,
    horizon_days: int = 0, embargo_days: int = 30,
) -> list[WalkForwardSplit]:
    """Convenience wrapper that sizes the initial window in years."""
    d = pd.to_datetime(pd.Series(list(dates)))
    span_days = (d.max() - d.min()).days
    if span_days < initial_train_years * 365:
        initial = max(252, len(d) // 3)
    else:
        # Approximate trading days = 252 per year
        initial = min(len(d) - step_days * 4, initial_train_years * 252)
    sp = WalkForwardSplitter(
        initial_train_size=initial,
        step_days=step_days,
        test_size_days=step_days,
        horizon_days=horizon_days,
        embargo_days=embargo_days,
    )
    return list(sp.split(d))

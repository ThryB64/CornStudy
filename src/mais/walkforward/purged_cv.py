"""V7-02 — Purged CV avec embargo : 9 protocoles comparés."""

from __future__ import annotations

from collections.abc import Generator, Iterator

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

SplitGen = Generator[tuple[np.ndarray, np.ndarray], None, None]


def classic(n: int, n_splits: int = 5) -> SplitGen:
    """Walk-forward classique sans embargo."""
    tss = TimeSeriesSplit(n_splits=n_splits)
    yield from tss.split(np.arange(n))


def embargo_h(
    dates: pd.DatetimeIndex,
    embargo_days: int,
    n_splits: int = 5,
) -> SplitGen:
    """Walk-forward + embargo H jours entre train et test."""
    tss = TimeSeriesSplit(n_splits=n_splits)
    for train_idx, test_idx in tss.split(np.arange(len(dates))):
        if len(train_idx) == 0:
            continue
        cutoff = dates[train_idx[-1]] + pd.Timedelta(days=embargo_days)
        test_purged = np.array([i for i in test_idx if dates[i] > cutoff])
        if len(test_purged) >= 5:
            yield train_idx, test_purged


def embargo_2h(
    dates: pd.DatetimeIndex,
    horizon_days: int,
    n_splits: int = 5,
) -> SplitGen:
    """Walk-forward + embargo 2×H jours."""
    yield from embargo_h(dates, 2 * horizon_days, n_splits)


def non_overlap(
    dates: pd.DatetimeIndex,
    horizon_days: int,
    n_splits: int = 5,
) -> SplitGen:
    """1 observation par fenêtre de H jours (stride = H)."""
    stride = max(1, horizon_days)
    idx = np.arange(0, len(dates), stride)
    tss = TimeSeriesSplit(n_splits=n_splits)
    for train_sub, test_sub in tss.split(idx):
        yield idx[train_sub], idx[test_sub]


def leave_one_year(dates: pd.DatetimeIndex) -> SplitGen:
    """Validation croisée : laisser une année entière en test."""
    years = sorted(dates.year.unique())
    for year in years[1:]:  # skip first year (train trop court)
        test_mask = dates.year == year
        train_mask = dates < dates[test_mask].min() - pd.Timedelta(days=7)
        train_idx = np.where(train_mask)[0]
        test_idx = np.where(test_mask)[0]
        if len(train_idx) >= 50 and len(test_idx) >= 5:
            yield train_idx, test_idx


def _crop_year(d: pd.Timestamp) -> int:
    return d.year if d.month >= 9 else d.year - 1


def leave_one_crop_year(dates: pd.DatetimeIndex) -> SplitGen:
    """Validation par crop year (septembre → août)."""
    crop_years = np.array([_crop_year(d) for d in dates])
    unique_cy = sorted(set(crop_years))
    for cy in unique_cy[1:]:  # skip first crop year
        test_mask = crop_years == cy
        train_mask = crop_years < cy
        train_idx = np.where(train_mask)[0]
        test_idx = np.where(test_mask)[0]
        if len(train_idx) >= 50 and len(test_idx) >= 5:
            yield train_idx, test_idx


def leave_one_crisis(dates: pd.DatetimeIndex) -> SplitGen:
    """Laisser une crise en test : 2012, 2020, 2022."""
    crisis_periods = [
        (pd.Timestamp("2012-01-01"), pd.Timestamp("2012-12-31")),
        (pd.Timestamp("2020-01-01"), pd.Timestamp("2020-12-31")),
        (pd.Timestamp("2022-01-01"), pd.Timestamp("2022-12-31")),
    ]
    for start, end in crisis_periods:
        test_mask = (dates >= start) & (dates <= end)
        train_mask = dates < start
        train_idx = np.where(train_mask)[0]
        test_idx = np.where(test_mask)[0]
        if len(train_idx) >= 100 and len(test_idx) >= 5:
            yield train_idx, test_idx


def block_bootstrap(
    dates: pd.DatetimeIndex,
    block_size: int = 63,
    n_iter: int = 10,
    test_frac: float = 0.2,
    seed: int = 42,
) -> SplitGen:
    """Block bootstrap : blocs consécutifs de block_size jours."""
    rng = np.random.default_rng(seed)
    n = len(dates)
    n_test = int(n * test_frac)
    n_blocks = max(1, n_test // block_size)
    for _ in range(n_iter):
        starts = rng.integers(0, n - block_size, size=n_blocks)
        test_idx_set = set()
        for s in starts:
            test_idx_set.update(range(int(s), min(int(s) + block_size, n)))
        test_idx = np.array(sorted(test_idx_set))
        train_idx = np.setdiff1d(np.arange(n), test_idx)
        if len(train_idx) >= 100 and len(test_idx) >= 5:
            yield train_idx, test_idx


def purged_kfold(
    dates: pd.DatetimeIndex,
    embargo_days: int,
    n_splits: int = 5,
) -> SplitGen:
    """Purged K-fold : folds temporels avec embargo entre train et test."""
    fold_size = len(dates) // (n_splits + 1)
    for k in range(n_splits):
        test_start_i = (k + 1) * fold_size
        test_end_i = min(test_start_i + fold_size, len(dates))
        test_idx = np.arange(test_start_i, test_end_i)
        cutoff_before = dates[test_start_i] - pd.Timedelta(days=embargo_days)
        cutoff_after = dates[test_end_i - 1] + pd.Timedelta(days=embargo_days) if test_end_i < len(dates) else dates[-1] + pd.Timedelta(days=9999)
        train_idx = np.array([
            i for i in range(len(dates))
            if i not in set(test_idx)
            and not (dates[i] >= cutoff_before and dates[i] <= cutoff_after)
        ])
        if len(train_idx) >= 50 and len(test_idx) >= 5:
            yield train_idx, test_idx


def get_protocol(
    name: str,
    dates: pd.DatetimeIndex,
    horizon_days: int = 90,
    n_splits: int = 5,
    embargo_days: int | None = None,
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Factory pour obtenir un protocole par nom."""
    emb = embargo_days if embargo_days is not None else horizon_days
    protocols = {
        "classic": lambda: classic(len(dates), n_splits),
        "embargo_H": lambda: embargo_h(dates, emb, n_splits),
        "embargo_2H": lambda: embargo_2h(dates, horizon_days, n_splits),
        "non_overlap": lambda: non_overlap(dates, horizon_days, n_splits),
        "block_bootstrap": lambda: block_bootstrap(dates),
        "leave_one_year": lambda: leave_one_year(dates),
        "leave_one_crop_year": lambda: leave_one_crop_year(dates),
        "leave_one_crisis": lambda: leave_one_crisis(dates),
        "purged_kfold": lambda: purged_kfold(dates, emb, n_splits),
    }
    if name not in protocols:
        raise ValueError(f"Protocole inconnu: '{name}'. Disponibles: {sorted(protocols)}")
    return protocols[name]()


ALL_PROTOCOLS = [
    "classic",
    "embargo_H",
    "embargo_2H",
    "non_overlap",
    "block_bootstrap",
    "leave_one_year",
    "leave_one_crop_year",
    "leave_one_crisis",
    "purged_kfold",
]

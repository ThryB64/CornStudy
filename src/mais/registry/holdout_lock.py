"""V8-INFRA-HOLDOUT — verrouillage physique du holdout 2024.

Mécanisme :
- `write_lock(dataset_path)` calcule sha256 du dataset et écrit `holdout_lock.json`.
- `read_lock()` retourne le lock courant ou None.
- `assert_no_holdout(df_or_index)` vérifie qu'aucune date n'est dans la fenêtre holdout.
- `is_holdout_unlocked(human_signature)` retourne True uniquement si signature explicite.

Le holdout est utilisé une seule fois en fin d'étude (V8-INDICATOR-DESIGN).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from mais.paths import ARTEFACTS_DIR

HOLDOUT_RANGE: tuple[str, str] = ("2024-01-01", "2024-12-31")
HOLDOUT_LOCK_PATH: Path = ARTEFACTS_DIR / "v8" / "holdout_lock.json"


class HoldoutLeakageError(RuntimeError):
    """Raised when a dataset or index contains dates from the locked holdout."""


def _sha256_file(path: Path, chunk: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def write_lock(
    dataset_path: Path,
    human_signature: str = "claude-v8-setup",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Écrit le fichier de verrouillage du holdout 2024."""
    HOLDOUT_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "lock_date": datetime.now(timezone.utc).isoformat(),
        "holdout_range": list(HOLDOUT_RANGE),
        "dataset_path": str(dataset_path),
        "dataset_sha256": _sha256_file(dataset_path) if dataset_path.exists() else None,
        "signature_human": human_signature,
        "version": "V8",
        "purpose": "holdout 2024 réservé pour validation finale, jamais utilisé en train/OOF",
    }
    if extra:
        payload["extra"] = extra
    HOLDOUT_LOCK_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return payload


def read_lock() -> dict[str, Any] | None:
    if not HOLDOUT_LOCK_PATH.exists():
        return None
    return json.loads(HOLDOUT_LOCK_PATH.read_text(encoding="utf-8"))


def assert_no_holdout(obj: pd.DataFrame | pd.Series | pd.DatetimeIndex) -> None:
    """Vérifie qu'aucune date de `obj` n'est dans HOLDOUT_RANGE.

    Accepte un DataFrame indexé par dates, une Series indexée par dates,
    ou un DatetimeIndex.
    """
    if isinstance(obj, pd.DatetimeIndex):
        idx = obj
    elif isinstance(obj, (pd.DataFrame, pd.Series)):
        if not isinstance(obj.index, pd.DatetimeIndex):
            return  # rien à vérifier si l'index n'est pas temporel
        idx = obj.index
    else:
        return

    start, end = pd.Timestamp(HOLDOUT_RANGE[0]), pd.Timestamp(HOLDOUT_RANGE[1])
    in_holdout = (idx >= start) & (idx <= end)
    n_violations = int(in_holdout.sum())
    if n_violations > 0:
        sample = idx[in_holdout][:5].tolist()
        raise HoldoutLeakageError(
            f"V8 HOLDOUT LEAKAGE: {n_violations} dates dans la fenêtre {HOLDOUT_RANGE}. "
            f"Exemples: {sample}. Utilisez `is_holdout_unlocked(...)` pour autorisation explicite."
        )


def is_holdout_unlocked(human_signature: str) -> bool:
    """Retourne True uniquement si la signature humaine matche un déverrouillage explicite.

    Le déverrouillage doit être documenté dans le lock (champ `unlocks`).
    """
    lock = read_lock()
    if lock is None:
        return False
    unlocks = lock.get("unlocks", [])
    return any(u.get("signature_human") == human_signature for u in unlocks)

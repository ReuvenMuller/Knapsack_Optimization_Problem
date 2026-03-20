from __future__ import annotations

import json
import os
import re
from typing import Any


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return cleaned.strip("_") or "value"


def build_cache_path(
    merged_dataset_path: str,
    utility_method: str,
    semantic_model_name: str,
    alpha: float,
    beta: float,
) -> str:
    abs_path = os.path.abspath(merged_dataset_path)
    stat = os.stat(abs_path)
    dataset_name = _slugify(os.path.splitext(os.path.basename(abs_path))[0])
    model_name = _slugify(semantic_model_name)
    signature = f"{stat.st_size}_{stat.st_mtime_ns}"
    filename = (
        f"{dataset_name}__{utility_method}__{model_name}__"
        f"a{alpha:.3f}_b{beta:.3f}__{signature}.json"
    )
    return os.path.join(os.path.dirname(abs_path), "cache", filename)


def load_utility_cache(path: str) -> dict[str, list[float]]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        payload: dict[str, Any] = json.load(handle)
    entries = payload.get("entries", {})
    return {str(key): [float(x) for x in values] for key, values in entries.items()}


def save_utility_cache(
    path: str,
    entries: dict[str, list[float]],
    metadata: dict[str, Any],
) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "metadata": metadata,
        "entries": entries,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)

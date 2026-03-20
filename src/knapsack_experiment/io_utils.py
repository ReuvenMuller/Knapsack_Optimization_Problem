from __future__ import annotations

import csv
import json
import os
from collections import defaultdict
from statistics import mean
from typing import Any


def ensure_dir(path: str) -> None:
    if not path:
        return
    os.makedirs(path, exist_ok=True)


def write_json(path: str, payload: dict[str, Any]) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def write_csv(path: str, rows: list[dict[str, Any]]) -> None:
    ensure_dir(os.path.dirname(path))
    if not rows:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write("")
        return

    columns = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Aggregate per (merge_size, budget_tokens) with means.
    """
    groups: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        merge_size = int(record["merge_size"])
        budget = int(record["budget_tokens"])
        groups[(merge_size, budget)].append(record)

    summary: list[dict[str, Any]] = []
    for (merge_size, budget), rows in sorted(groups.items()):
        summary.append(
            {
                "merge_size": merge_size,
                "budget_tokens": budget,
                "num_instances": len(rows),
                "avg_runtime_sec": mean(float(r["runtime_sec"]) for r in rows),
                "avg_selected_utility": mean(float(r["selected_utility"]) for r in rows),
                "avg_support_recall": mean(float(r["support_recall"]) for r in rows),
                "avg_exact_support_coverage": mean(
                    float(r["exact_support_coverage"]) for r in rows
                ),
                "avg_budget_utilization": mean(float(r["budget_utilization"]) for r in rows),
                "avg_compression_ratio": mean(float(r["compression_ratio"]) for r in rows),
                "avg_selected_chunks": mean(float(r["selected_chunks"]) for r in rows),
                "avg_total_chunks": mean(float(r["total_chunks"]) for r in rows),
                "avg_optimality_gap": mean(float(r["optimality_gap"]) for r in rows)
                if all("optimality_gap" in r for r in rows)
                else None,
            }
        )
    return summary

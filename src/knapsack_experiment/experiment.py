from __future__ import annotations

import math
import os
import time
from datetime import datetime, timezone
from typing import Any

from .evaluation import compute_selection_metrics
from .hotpot import load_merged_jsonl
from .solvers import solve_by_name, solve_exact_dp
from .utility import compute_utilities
from .utility_cache import build_cache_path, load_utility_cache, save_utility_cache


def _scale_costs(costs: list[int], budget: int, divisor: int) -> tuple[list[int], int]:
    if divisor <= 1:
        return costs, budget
    scaled_costs = [max(1, math.ceil(cost / divisor)) for cost in costs]
    scaled_budget = max(1, math.ceil(budget / divisor))
    return scaled_costs, scaled_budget


def run_algorithm_experiment(
    merged_dataset_path: str,
    algorithm: str,
    budgets: list[int],
    utility_method: str,
    utility_alpha: float = 0.7,
    utility_beta: float = 0.3,
    semantic_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    dp_cost_scale: int = 1,
    max_instances: int | None = None,
    compute_optimality_gap: bool = False,
    local_search_iterations: int = 50,
    local_search_candidate_pool: int = 300,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    instances = load_merged_jsonl(merged_dataset_path)
    if max_instances is not None:
        instances = instances[:max_instances]

    cache_path = build_cache_path(
        merged_dataset_path=merged_dataset_path,
        utility_method=utility_method,
        semantic_model_name=semantic_model_name,
        alpha=utility_alpha,
        beta=utility_beta,
    )
    utility_cache = load_utility_cache(cache_path)
    cache_dirty = False

    records: list[dict[str, Any]] = []
    run_meta: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "algorithm": algorithm,
        "budgets": budgets,
        "utility_method": utility_method,
        "utility_alpha": utility_alpha,
        "utility_beta": utility_beta,
        "semantic_model_name": semantic_model_name,
        "dp_cost_scale": dp_cost_scale,
        "num_instances": len(instances),
        "compute_optimality_gap": compute_optimality_gap,
        "local_search_iterations": local_search_iterations,
        "local_search_candidate_pool": local_search_candidate_pool,
        "merged_dataset_path": merged_dataset_path,
        "utility_cache_path": cache_path,
    }

    for instance in instances:
        texts = [chunk.text for chunk in instance.chunks]
        raw_costs = [chunk.token_cost for chunk in instance.chunks]
        support_flags = [chunk.is_gold_support for chunk in instance.chunks]

        if instance.merged_id in utility_cache:
            utilities = utility_cache[instance.merged_id]
        else:
            utilities = compute_utilities(
                query=instance.question,
                chunks=texts,
                method=utility_method,
                semantic_model_name=semantic_model_name,
                alpha=utility_alpha,
                beta=utility_beta,
            )
            utility_cache[instance.merged_id] = utilities
            cache_dirty = True

        for budget in budgets:
            if algorithm == "exact_dp":
                scaled_costs, scaled_budget = _scale_costs(raw_costs, budget, dp_cost_scale)
            else:
                scaled_costs = raw_costs
                scaled_budget = budget

            started = time.perf_counter()
            result = solve_by_name(
                algorithm=algorithm,
                costs=scaled_costs,
                utilities=utilities,
                budget=scaled_budget,
                local_search_iterations=local_search_iterations,
                local_search_candidate_pool=local_search_candidate_pool,
            )
            runtime_sec = time.perf_counter() - started

            metrics = compute_selection_metrics(
                selected_indices=result.selected_indices,
                costs=raw_costs,
                utilities=utilities,
                gold_support_flags=support_flags,
                budget=budget,
            )

            record: dict[str, Any] = {
                "algorithm": algorithm,
                "merged_id": instance.merged_id,
                "merge_size": instance.merge_size,
                "target_example_id": instance.target_example_id,
                "budget_tokens": budget,
                "budget_scaled": scaled_budget,
                "dp_cost_scale": dp_cost_scale if algorithm == "exact_dp" else 1,
                "utility_method": utility_method,
                "runtime_sec": runtime_sec,
                **metrics,
            }

            if compute_optimality_gap and algorithm != "exact_dp":
                optimal_scaled_costs, optimal_scaled_budget = _scale_costs(
                    raw_costs, budget, dp_cost_scale
                )
                optimal = solve_exact_dp(
                    costs=optimal_scaled_costs,
                    utilities=utilities,
                    budget=optimal_scaled_budget,
                )
                optimal_utility = sum(utilities[idx] for idx in optimal.selected_indices)
                gap = (
                    (optimal_utility - metrics["selected_utility"]) / optimal_utility
                    if optimal_utility > 1e-12
                    else 0.0
                )
                record["optimal_utility"] = optimal_utility
                record["optimality_gap"] = gap

            records.append(record)

    if cache_dirty:
        save_utility_cache(
            path=cache_path,
            entries=utility_cache,
            metadata={
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "merged_dataset_path": os.path.abspath(merged_dataset_path),
                "utility_method": utility_method,
                "semantic_model_name": semantic_model_name,
                "utility_alpha": utility_alpha,
                "utility_beta": utility_beta,
            },
        )

    return records, run_meta

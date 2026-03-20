from __future__ import annotations


def compute_selection_metrics(
    selected_indices: list[int],
    costs: list[int],
    utilities: list[float],
    gold_support_flags: list[bool],
    budget: int,
) -> dict[str, float]:
    selected_set = set(selected_indices)
    total_cost = sum(costs)
    selected_cost = sum(costs[idx] for idx in selected_set)
    selected_utility = sum(utilities[idx] for idx in selected_set)

    support_total = sum(1 for flag in gold_support_flags if flag)
    support_selected = sum(
        1 for idx, is_support in enumerate(gold_support_flags) if is_support and idx in selected_set
    )
    support_recall = (
        float(support_selected) / float(support_total) if support_total > 0 else 0.0
    )
    exact_support_coverage = 1.0 if support_total > 0 and support_selected == support_total else 0.0

    return {
        "total_chunks": float(len(costs)),
        "total_cost_tokens": float(total_cost),
        "selected_chunks": float(len(selected_set)),
        "selected_cost_tokens": float(selected_cost),
        "budget_utilization": float(selected_cost) / float(budget) if budget > 0 else 0.0,
        "compression_ratio": float(selected_cost) / float(total_cost) if total_cost > 0 else 0.0,
        "selected_utility": selected_utility,
        "support_total": float(support_total),
        "support_selected": float(support_selected),
        "support_recall": support_recall,
        "exact_support_coverage": exact_support_coverage,
    }

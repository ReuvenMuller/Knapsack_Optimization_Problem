from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SolverResult:
    selected_indices: list[int]
    objective_value: float


def _selected_utility(selected: set[int], utilities: list[float]) -> float:
    return sum(utilities[idx] for idx in selected)


def _selected_cost(selected: set[int], costs: list[int]) -> int:
    return sum(costs[idx] for idx in selected)


def solve_exact_dp(costs: list[int], utilities: list[float], budget: int) -> SolverResult:
    """
    Exact 0/1 knapsack with O(n * budget) time.
    Uses 1D DP + per-item keep flags for efficient reconstruction.
    """
    n = len(costs)
    dp = [0.0] * (budget + 1)
    keep = [bytearray(budget + 1) for _ in range(n)]

    for idx in range(n):
        cost = costs[idx]
        util = utilities[idx]
        if cost > budget:
            continue
        row = keep[idx]
        for b in range(budget, cost - 1, -1):
            candidate = dp[b - cost] + util
            if candidate > dp[b]:
                dp[b] = candidate
                row[b] = 1

    end_budget = max(range(budget + 1), key=lambda b: dp[b])
    selected: list[int] = []
    b = end_budget
    for idx in range(n - 1, -1, -1):
        if b <= 0:
            break
        if keep[idx][b]:
            selected.append(idx)
            b -= costs[idx]
    selected.reverse()
    return SolverResult(selected_indices=selected, objective_value=dp[end_budget])


def solve_greedy_ratio(costs: list[int], utilities: list[float], budget: int) -> SolverResult:
    """
    Greedy by utility / cost ratio.
    """
    order = sorted(
        range(len(costs)),
        key=lambda idx: (utilities[idx] / max(1, costs[idx]), utilities[idx]),
        reverse=True,
    )

    selected: list[int] = []
    remaining = budget
    value = 0.0
    for idx in order:
        cost = costs[idx]
        if cost <= remaining:
            selected.append(idx)
            remaining -= cost
            value += utilities[idx]
    return SolverResult(selected_indices=selected, objective_value=value)


def solve_greedy_refine(
    costs: list[int],
    utilities: list[float],
    budget: int,
    max_iterations: int = 50,
    candidate_pool_size: int = 300,
) -> SolverResult:
    """
    Greedy initialization + local search with add and 1-for-1 swap moves.
    """
    initial = solve_greedy_ratio(costs, utilities, budget)
    selected: set[int] = set(initial.selected_indices)

    for _ in range(max_iterations):
        improved = False
        current_cost = _selected_cost(selected, costs)
        current_value = _selected_utility(selected, utilities)

        # 1) Try a direct add move.
        remaining = budget - current_cost
        best_add_idx = None
        best_add_gain = 0.0
        for idx in range(len(costs)):
            if idx in selected:
                continue
            if costs[idx] <= remaining and utilities[idx] > best_add_gain:
                best_add_gain = utilities[idx]
                best_add_idx = idx
        if best_add_idx is not None:
            selected.add(best_add_idx)
            improved = True
            continue

        # 2) Try best 1-for-1 swap among top unselected candidates.
        unselected = [idx for idx in range(len(costs)) if idx not in selected]
        unselected.sort(
            key=lambda idx: (utilities[idx] / max(1, costs[idx]), utilities[idx]),
            reverse=True,
        )
        candidate_unselected = unselected[:candidate_pool_size]

        best_swap_in = None
        best_swap_out = None
        best_swap_gain = 0.0
        for add_idx in candidate_unselected:
            add_cost = costs[add_idx]
            add_util = utilities[add_idx]
            for rem_idx in selected:
                new_cost = current_cost - costs[rem_idx] + add_cost
                if new_cost > budget:
                    continue
                gain = add_util - utilities[rem_idx]
                if gain > best_swap_gain + 1e-12:
                    best_swap_gain = gain
                    best_swap_in = add_idx
                    best_swap_out = rem_idx

        if best_swap_in is not None and best_swap_out is not None:
            selected.remove(best_swap_out)
            selected.add(best_swap_in)
            improved = True

        if not improved:
            break

    final_indices = sorted(selected)
    final_value = sum(utilities[idx] for idx in final_indices)
    return SolverResult(selected_indices=final_indices, objective_value=final_value)


def solve_bruteforce(
    costs: list[int],
    utilities: list[float],
    budget: int,
) -> SolverResult:
    """
    Exhaustive subset enumeration (2^n).
    """
    n = len(costs)
    best_value = -1.0
    best_mask = 0
    total_masks = 1 << n

    for mask in range(total_masks):
        cost_sum = 0
        value_sum = 0.0
        feasible = True
        bit = mask
        idx = 0
        while bit:
            if bit & 1:
                cost_sum += costs[idx]
                if cost_sum > budget:
                    feasible = False
                    break
                value_sum += utilities[idx]
            idx += 1
            bit >>= 1
        if feasible and value_sum > best_value:
            best_value = value_sum
            best_mask = mask

    selected: list[int] = []
    for idx in range(n):
        if (best_mask >> idx) & 1:
            selected.append(idx)
    return SolverResult(selected_indices=selected, objective_value=max(best_value, 0.0))


def solve_by_name(
    algorithm: str,
    costs: list[int],
    utilities: list[float],
    budget: int,
    local_search_iterations: int = 50,
    local_search_candidate_pool: int = 300,
) -> SolverResult:
    algorithm = algorithm.lower()
    if algorithm == "exact_dp":
        return solve_exact_dp(costs, utilities, budget)
    if algorithm == "bruteforce":
        return solve_bruteforce(costs, utilities, budget)
    if algorithm == "greedy_ratio":
        return solve_greedy_ratio(costs, utilities, budget)
    if algorithm == "greedy_refine":
        return solve_greedy_refine(
            costs,
            utilities,
            budget,
            max_iterations=local_search_iterations,
            candidate_pool_size=local_search_candidate_pool,
        )
    raise ValueError(
        f"Unknown algorithm '{algorithm}'. "
        "Supported: bruteforce, exact_dp, greedy_ratio, greedy_refine"
    )

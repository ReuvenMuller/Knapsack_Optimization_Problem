def solve_exact_dp(costs, utilities, budget):
    """
    Standard 0/1 knapsack solved via dynamic programming.
 
    Each chunk is either included or not (hence 0/1), and the goal is to
    maximize total utility without going over the token budget. This is the
    classic O(n * W) DP formulation where W is the budget.
 
    To recover which items were actually chosen, we store a keep[i][b] flag
    per item per capacity. A bit wasteful in memory but makes backtracking
    straightforward, didn't want to re-run the DP or store full parent tables.
    """
    n = len(costs)
 
    # dp[b] = best utility reachable using at most b tokens
    dp = [0.0] * (budget + 1)
 
    # track which item was "taken" at each (item, capacity) state for traceback
    # bytearray is compact enough for large budgets
    keep = [bytearray(budget + 1) for _ in range(n)]
 
    for i in range(n):
        c = costs[i]
        u = utilities[i]
 
        # nothing we can do if a single chunk already exceeds the full budget
        if c > budget:
            continue
 
        # go right-to-left so each item is only considered once (standard 0/1 trick)
        for b in range(budget, c - 1, -1):
            if dp[b - c] + u > dp[b]:
                dp[b] = dp[b - c] + u
                keep[i][b] = 1
 
    # best achievable value might not land exactly at `budget` tokens used
    best_b = 0
    for b in range(budget + 1):
        if dp[b] > dp[best_b]:
            best_b = b
 
    # backtrack from best_b to figure out which chunks were actually selected
    selected = []
    b = best_b
    for i in range(n - 1, -1, -1):
        if b <= 0:
            break
        if keep[i][b]:
            selected.append(i)
            b -= costs[i]
 
    selected.reverse()
    return selected
 
 
def solve_greedy_ratio(costs, utilities, budget):
    # order = sorted(
    #     range(len(costs)),
    #     key=lambda idx: (utilities[idx] / max(1, costs[idx]), utilities[idx]),
    #     reverse=True,
    # )

    # selected = []
    # remaining = budget
    # value = 0.0
    # for idx in order:
    #     cost = costs[idx]
    #     if cost <= remaining:
    #         selected.append(idx)
    #         remaining -= cost
    #         value += utilities[idx]
    # return selected, value
    pass


def solve_greedy_refine(costs, utilities, budget, max_iterations=50, candidate_pool_size=300):
    # initial_selected, _ = solve_greedy_ratio(costs, utilities, budget)
    # selected = set(initial_selected)

    # for _ in range(max_iterations):
    #     improved = False
    #     current_cost = sum(costs[idx] for idx in selected)

    #     remaining = budget - current_cost
    #     best_add_idx = None
    #     best_add_gain = 0.0
    #     for idx in range(len(costs)):
    #         if idx in selected:
    #             continue
    #         if costs[idx] <= remaining and utilities[idx] > best_add_gain:
    #             best_add_gain = utilities[idx]
    #             best_add_idx = idx
    #     if best_add_idx is not None:
    #         selected.add(best_add_idx)
    #         improved = True
    #         continue

    #     unselected = [idx for idx in range(len(costs)) if idx not in selected]
    #     unselected.sort(
    #         key=lambda idx: (utilities[idx] / max(1, costs[idx]), utilities[idx]),
    #         reverse=True,
    #     )
    #     candidate_unselected = unselected[:candidate_pool_size]

    #     best_swap_in = None
    #     best_swap_out = None
    #     best_swap_gain = 0.0
    #     for add_idx in candidate_unselected:
    #         add_cost = costs[add_idx]
    #         add_util = utilities[add_idx]
    #         for rem_idx in selected:
    #             new_cost = current_cost - costs[rem_idx] + add_cost
    #             if new_cost > budget:
    #                 continue
    #             gain = add_util - utilities[rem_idx]
    #             if gain > best_swap_gain + 1e-12:
    #                 best_swap_gain = gain
    #                 best_swap_in = add_idx
    #                 best_swap_out = rem_idx

    #     if best_swap_in is not None and best_swap_out is not None:
    #         selected.remove(best_swap_out)
    #         selected.add(best_swap_in)
    #         improved = True

    #     if not improved:
    #         break

    # final_indices = sorted(selected)
    # final_value = sum(utilities[idx] for idx in final_indices)
    # return final_indices, final_value
    pass

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
 
 
def solve_greedy_ratio(costs, utility_scores, budget):
    # Greedy Algorithm for 0-1 Knapsack - does not guarantee an optimal result
    # input is an list of costs and a list of utlility score + overall budget ( cost cap )
    # idx is the index value for the associate object

    # Sort chunks in order of best utility/cost ration
    # lambda function determines next value by taking next highest utility/cost or taking the next highest utility if cost/utility is a tie
    # max(1, costs [idx]) = prevents division by zero)

    ordered_chunks = sorted(
         range(len(costs)),
         key=lambda idx: (utility_scores[idx] / max(1, costs[idx]), utility_scores[idx]),
         reverse=True,
    )

    # initialize list of selected chunks, remaining_budget, and overall value
    selected = []
    remaining_budget = budget
    value = 0.0

    # review each chunk in descending order,
    # if cost is less than or equal to the remaining budget, add to selected, decrease remaining budget by cost, and increase value by utility
    # otherwise proceed to next chunk
    for idx in ordered_chunks:
        chunk_cost = costs[idx]
        if chunk_cost <= remaining_budget:
            selected.append(idx)
            remaining_budget -= chunk_cost
            value += utility_scores[idx]
    # return selected, value
    return selected


def solve_greedy_refine(
    costs,
    utilities,
    budget,
    max_iterations=50,
    candidate_pool_size=300,
    remove_pool_size=100,
):
    """
    Improve the greedy-ratio solution with bounded local swaps.
    """
    selected = solve_greedy_ratio(costs, utilities, budget)

    for _ in range(max_iterations):
        changed = False

        total_cost = 0
        for i in selected:
            total_cost += costs[i]

        unselected = []
        for i in range(len(costs)):
            if i not in selected:
                unselected.append(i)

        unselected.sort(key=lambda i: utilities[i] / costs[i], reverse=True)
        possible_adds = unselected[:candidate_pool_size]

        possible_removes = selected.copy()
        possible_removes.sort(key=lambda i: utilities[i] / costs[i])
        possible_removes = possible_removes[:remove_pool_size]

        item_to_add = None
        item_to_remove = None
        best_gain = 0.0

        # Try the best add/remove candidates instead of every possible swap.
        for add_i in possible_adds:
            for remove_i in possible_removes:
                new_cost = total_cost - costs[remove_i] + costs[add_i]
                gain = utilities[add_i] - utilities[remove_i]

                if new_cost <= budget and gain > best_gain:
                    item_to_add = add_i
                    item_to_remove = remove_i
                    best_gain = gain

        if item_to_add is not None:
            selected.remove(item_to_remove)
            selected.append(item_to_add)
            changed = True

        if changed:
            total_cost = 0
            for i in selected:
                total_cost += costs[i]

            best_extra_item = None
            best_extra_utility = 0.0

            for i in range(len(costs)):
                if i in selected:
                    continue

                if total_cost + costs[i] <= budget and utilities[i] > best_extra_utility:
                    best_extra_item = i
                    best_extra_utility = utilities[i]

            if best_extra_item is not None:
                selected.append(best_extra_item)

        if not changed:
            break

    selected.sort()
    return selected

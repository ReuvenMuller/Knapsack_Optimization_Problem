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


# -------------------------------------------------------------------------
# Greedy Refine Algorithm: high-level overview
#
# Greedy ratio gives us a quick first answer, but sometimes it misses better
# choices. Greedy refine starts with the greedy answer and then tries to improve
# it using small local changes.
#
# The refinement idea is:
# 1. Start with the chunks selected by solve_greedy_ratio.
# 2. Try a swap:
#    remove one selected chunk and add one unselected chunk.
# 3. To keep this faster, do not try every possible swap.
#    Instead:
#    - only try adding strong unselected chunks
#    - only try removing weak selected chunks
# 4. After a swap, try to add one extra chunk if there is leftover room.
# 5. Repeat this process a limited number of times.
#
# This is still much simpler than exact DP. It does not try all possible
# combinations. It only tries small improvements to the greedy answer.
# -------------------------------------------------------------------------
def solve_greedy_refine(
    costs,
    utilities,
    budget,
    max_iterations=50,
    candidate_pool_size=300,
    remove_pool_size=100,
):
    """
    Greedy refine algorithm.

    Start with the greedy answer. Then try to make it better by:
    1. swapping one weak selected chunk for one strong unselected chunk
    2. adding a chunk after a swap if extra room becomes available
    """
    # First get the starting solution from the greedy ratio algorithm.
    # This gives us a reasonable answer to improve.
    selected = solve_greedy_ratio(costs, utilities, budget)

    # Try to improve the answer a limited number of times.
    # max_iterations prevents the loop from running forever.
    for _ in range(max_iterations):
        # changed tells us whether this loop made the solution better.
        # If nothing changes, we stop.
        changed = False

        # Recalculate the current total cost of the selected chunks.
        total_cost = 0

        for i in selected:
            total_cost += costs[i]

        # Step 1: build a list of chunks that are NOT selected.
        #
        # These are the chunks we might want to add.
        unselected = []

        for i in range(len(costs)):
            if i not in selected:
                unselected.append(i)

        # Step 2: sort unselected chunks from strongest to weakest.
        #
        # A strong chunk has high utility per token.
        # These are good candidates to add.
        unselected.sort(key=lambda i: utilities[i] / costs[i], reverse=True)

        # Only look at the top unselected chunks.
        # This makes the algorithm faster than checking everything.
        possible_adds = unselected[:candidate_pool_size]

        # Step 3: sort selected chunks from weakest to strongest.
        #
        # A weak selected chunk has low utility per token.
        # These are good candidates to remove.
        possible_removes = selected.copy()
        possible_removes.sort(key=lambda i: utilities[i] / costs[i])

        # Only look at the weakest selected chunks.
        possible_removes = possible_removes[:remove_pool_size]

        # Step 4: try to find the best swap from these smaller lists.
        #
        # A swap means:
        # - remove one chunk we already selected
        # - add one chunk we did not select
        #
        # We only accept a swap if:
        # - the new total cost is within the budget
        # - the new chunk has more utility than the removed chunk
        item_to_add = None
        item_to_remove = None
        best_gain = 0.0

        # Try strong chunks as possible additions.
        for add_i in possible_adds:
            # Try weak chunks as possible removals.
            for remove_i in possible_removes:
                # This is what the total cost would be after the swap.
                new_cost = total_cost - costs[remove_i] + costs[add_i]

                # This is how much utility changes after the swap.
                # Positive means the swap improves the solution.
                gain = utilities[add_i] - utilities[remove_i]

                # If this swap is the best improvement so far, remember it.
                if new_cost <= budget and gain > best_gain:
                    item_to_add = add_i
                    item_to_remove = remove_i
                    best_gain = gain

        # If we found a valid improving swap, make the swap.
        if item_to_add is not None:
            selected.remove(item_to_remove)
            selected.append(item_to_add)
            changed = True

        # Step 5: after a swap, we may have extra room.
        #
        # Now it makes sense to check whether another chunk can fit.
        # We do this AFTER the swap, not before, because greedy already tried
        # to add chunks during the first pass.
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

        # If we did not swap anything,
        # there is no simple improvement left, so stop.
        if not changed:
            break

    # Return selected chunks in original document order.
    selected.sort()
    return selected

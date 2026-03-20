# Full Experiment Report

Generated on 2026-03-20T17:00:42.104233+00:00

## Setup

- Dataset: merged HotpotQA distractor validation set
- Total merged instances: 100
- Merge sizes: 10, 20, 30, 40, 50
- Budgets: 2000, 4000, 8000
- Algorithms: exact_dp, greedy_ratio, greedy_refine
- Utility method: lexical
- Fair comparison: all methods used raw token costs (`dp_cost_scale = 1`)

## Key Findings

- At the hardest reported setting (`merge_size = 50`, `budget = 8000`), `exact_dp` averaged 2.1355s, `greedy_ratio` averaged 0.0017s, and `greedy_refine` averaged 0.0187s.
- In that setting, `greedy_ratio` was about 1275x faster than `exact_dp`, and `greedy_refine` was about 114x faster.
- As budget increased from 2000 to 8000, runtime increased sharply for `exact_dp`, but only modestly for the greedy methods.
- `greedy_ratio` and `greedy_refine` had nearly identical utility/correctness summaries in these runs, which suggests the current local-search refinement often did not improve over the greedy starting solution.
- Support recall generally improved as the budget increased, across all methods.

## Runtime Graphs

![runtime_vs_merge_size_budget_2000.svg](C:\Users\reuve\OneDrive\Documents\Knapsack_Optimization_Problem\report\runtime_vs_merge_size_budget_2000.svg)

![runtime_vs_merge_size_budget_4000.svg](C:\Users\reuve\OneDrive\Documents\Knapsack_Optimization_Problem\report\runtime_vs_merge_size_budget_4000.svg)

![runtime_vs_merge_size_budget_8000.svg](C:\Users\reuve\OneDrive\Documents\Knapsack_Optimization_Problem\report\runtime_vs_merge_size_budget_8000.svg)

## Summary Tables

### exact_dp

[summary.csv](C:\Users\reuve\OneDrive\Documents\Knapsack_Optimization_Problem\results\exact_dp\fresh_full_exact_dp\summary.csv)

### greedy_ratio

[summary.csv](C:\Users\reuve\OneDrive\Documents\Knapsack_Optimization_Problem\results\greedy_ratio\fresh_full_greedy_ratio\summary.csv)

### greedy_refine

[summary.csv](C:\Users\reuve\OneDrive\Documents\Knapsack_Optimization_Problem\results\greedy_refine\fresh_full_greedy_refine\summary.csv)

## Interpretation

The runtime story is clean and matches the algorithmic intuition for this project. `exact_dp` gives the strongest exact baseline but scales worst as merge size and budget grow. `greedy_ratio` is extremely fast and appears to preserve most of the useful behavior at a tiny fraction of the runtime. `greedy_refine` adds extra computation over plain greedy, but under the current refinement strategy it did not materially improve the aggregate quality metrics in the full run.
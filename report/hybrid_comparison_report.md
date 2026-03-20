# Hybrid Utility Report

Generated on 2026-03-20T19:09:45.530475+00:00

## Summary

- Main focus: hybrid utility (`0.7 * semantic + 0.3 * lexical`) using `sentence-transformers/all-MiniLM-L6-v2`.
- Hybrid results are compared against the earlier lexical-only runs.
- At `merge_size = 50`, `budget = 8000`, hybrid `exact_dp` averaged 1.8256s, `greedy_ratio` averaged 0.0016s, and `greedy_refine` averaged 0.0529s.
- In that hardest hybrid setting, `greedy_ratio` was about 1125x faster than `exact_dp`, and `greedy_refine` was about 35x faster.
- Hybrid generally improved support recall and exact support coverage relative to lexical, especially at medium and high budgets.
- `greedy_ratio` and `greedy_refine` remained very close in quality, so the extra local-search cost did not translate into a large aggregate gain.

## Overall Lexical vs Hybrid Comparison

| Algorithm | Lexical Recall | Hybrid Recall | Lexical Exact Coverage | Hybrid Exact Coverage |
|---|---:|---:|---:|---:|
| exact_dp | 0.864 | 0.867 | 0.660 | 0.727 |
| greedy_ratio | 0.867 | 0.866 | 0.667 | 0.723 |
| greedy_refine | 0.867 | 0.866 | 0.667 | 0.723 |

## Figures

![runtime_2000](C:\Users\reuve\OneDrive\Documents\Knapsack_Optimization_Problem\report\figures\hybrid_runtime_budget_2000.png)

![runtime_4000](C:\Users\reuve\OneDrive\Documents\Knapsack_Optimization_Problem\report\figures\hybrid_runtime_budget_4000.png)

![runtime_8000](C:\Users\reuve\OneDrive\Documents\Knapsack_Optimization_Problem\report\figures\hybrid_runtime_budget_8000.png)

![greedy_only_8000](C:\Users\reuve\OneDrive\Documents\Knapsack_Optimization_Problem\report\figures\hybrid_greedy_only_budget_8000.png)

![coverage_compare](C:\Users\reuve\OneDrive\Documents\Knapsack_Optimization_Problem\report\figures\lexical_vs_hybrid_exact_coverage.png)

![recall_compare](C:\Users\reuve\OneDrive\Documents\Knapsack_Optimization_Problem\report\figures\lexical_vs_hybrid_support_recall.png)

# Knapsack Optimization (Streamlined)

This repository contains a streamlined knapsack-context-compression workflow built on HotpotQA (distractor setting).

## Files

- `build_merged_dataset.py`
  - Loads HotpotQA examples.
  - Merges examples into larger contexts.
  - Splits text into chunks.
  - Computes chunk utility.

- `utility.py`
  - Utility scoring functions (lexical, semantic, hybrid).

- `algorithms.py`
  - Exact dynamic programming knapsack solver.
  - Includes commented placeholders for additional algorithms.

- `run_algorithms.py`
  - Runs the experiment using exact DP.
  - Writes raw output to `results.csv`.

## How To Run

From the repository root:

```powershell
python .\run_algorithms.py
```

This will:
1. Load HotpotQA distractor validation examples.
2. Build merged instances.
3. Run exact DP at budgets `2000`, `4000`, and `8000`.
4. Write raw results to `results.csv`.

## Notes

- Chunk size is currently defined as whitespace-separated word count.
- Output is intentionally raw (`results.csv`) for downstream analysis.

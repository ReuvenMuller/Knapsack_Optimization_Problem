# Knapsack Optimization for LLM Context Compression

This project models LLM context compression as a 0/1 knapsack problem.
Text chunks are treated as items, chunk length is the cost, and relevance to
the question is the utility. The experiments use the HotpotQA distractor
validation split.

## Files

- `algorithms.py`
  - Exact dynamic programming knapsack solver.
  - Greedy ratio solver.
  - Greedy refinement solver.

- `build_merged_dataset.py`
  - Loads HotpotQA examples.
  - Merges examples into larger contexts.
  - Splits text into chunks.
  - Labels exact HotpotQA supporting sentences.
  - Computes chunk utility.

- `run_algorithms.py`
  - Runs all three algorithms.
  - Writes raw output to `results.csv`.

- `requirements.txt`
  - Python dependencies needed to run the project.

- `results.csv`
  - Saved raw experiment results.

- `analysis_outputs/chunk_utilities.csv`
  - Cached chunk utility dataset used by the runner.

- `utility.py`
  - Utility scoring functions (lexical, semantic, hybrid).

## How To Run

From the repository root:

```powershell
python -m pip install -r requirements.txt
python .\run_algorithms.py
```

This will:
1. Load HotpotQA distractor validation examples.
2. Build merged instances.
3. Reuse cached chunk utility scores from `analysis_outputs/chunk_utilities.csv` when the cached chunks match the rebuilt instances.
4. Compute utility scores only for new or changed merged instances.
5. Run Exact DP, Greedy Ratio, and Greedy Refine at budgets `2000`, `4000`, and `8000`.
6. Write raw results to `results.csv`.

Expected raw result size:

```text
3 algorithms x 180 merged instances x 3 budgets = 1620 rows
```

## Notes

- Chunk size is currently defined as whitespace-separated word count.
- Utility is a hybrid score: `0.75 * semantic + 0.25 * lexical`.
- Semantic scoring is cached by merged instance, so increasing `MERGE_SIZES` in
  `build_merged_dataset.py` reuses old scores and only scores the newly added
  instances.
- Runtime for the greedy algorithms is measured using repeated runs and the median time.

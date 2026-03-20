# LLM Context Compression as a Knapsack Problem

This repository implements a full experimental framework for your class project:

- Build merged HotpotQA distractor instances at controlled sizes.
- Chunk context by sentence (with period-based splitting).
- Compute chunk utility scores.
- Run knapsack solvers individually:
  - `bruteforce`
  - `exact_dp`
  - `greedy_ratio`
  - `greedy_refine`
- Save each algorithm run to a separate results folder.

## 1) Project Structure

```text
scripts/
  build_merged_dataset.py
  run_algorithm.py
  run_all_algorithms.py
src/knapsack_experiment/
  chunking.py
  evaluation.py
  experiment.py
  hotpot.py
  io_utils.py
  model.py
  solvers.py
  utility.py
requirements.txt
```

## 2) Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

Optional semantic utility support:

```powershell
pip install sentence-transformers
```

## 3) Build the Merged Dataset

This creates the 100-instance design (20 samples each for merge sizes 10/20/30/40/50):

```powershell
python .\scripts\build_merged_dataset.py `
  --source-config distractor `
  --source-split validation `
  --merge-sizes 10 20 30 40 50 `
  --samples-per-size 20 `
  --chunking-mode period `
  --seed 42 `
  --output-path .\data\merged_hotpotqa_distractor_validation.jsonl
```

If your Python launcher is `py`, use:

```powershell
py -3 .\scripts\build_merged_dataset.py ...
```

## 4) Run One Algorithm (Individually)

Run exact DP:

```powershell
python .\scripts\run_algorithm.py `
  --dataset-path .\data\merged_hotpotqa_distractor_validation.jsonl `
  --algorithm exact_dp `
  --utility-method lexical `
  --budgets 2000 4000 8000 `
  --dp-cost-scale 1 `
  --results-dir .\results
```

Run brute force (full exhaustive search):

```powershell
python .\scripts\run_algorithm.py `
  --dataset-path .\data\merged_hotpotqa_distractor_validation.jsonl `
  --algorithm bruteforce `
  --utility-method lexical `
  --budgets 2000 `
  --max-instances 1 `
  --results-dir .\results
```

Run greedy ratio:

```powershell
python .\scripts\run_algorithm.py `
  --dataset-path .\data\merged_hotpotqa_distractor_validation.jsonl `
  --algorithm greedy_ratio `
  --utility-method lexical `
  --budgets 2000 4000 8000 `
  --results-dir .\results
```

Run greedy + local refinement:

```powershell
python .\scripts\run_algorithm.py `
  --dataset-path .\data\merged_hotpotqa_distractor_validation.jsonl `
  --algorithm greedy_refine `
  --utility-method lexical `
  --budgets 2000 4000 8000 `
  --local-search-iterations 50 `
  --local-search-candidate-pool 300 `
  --results-dir .\results
```

## 5) Run All Algorithms in One Command

```powershell
python .\scripts\run_all_algorithms.py `
  --dataset-path .\data\merged_hotpotqa_distractor_validation.jsonl `
  --budgets 2000 4000 8000 `
  --utility-method lexical `
  --results-dir .\results `
  --run-tag baseline
```

## 6) Results Output Layout

Each algorithm is stored in its own directory:

```text
results/
  bruteforce/<run_name>/
    details.csv
    summary.csv
    run_config.json
  exact_dp/<run_name>/
    details.csv
    summary.csv
    run_config.json
  greedy_ratio/<run_name>/
    details.csv
    summary.csv
    run_config.json
  greedy_refine/<run_name>/
    details.csv
    summary.csv
    run_config.json
```

This gives you clean separation for per-algorithm analysis and plotting.

## 7) Utility Caching

Utility scores are now cached automatically by:

- merged dataset file
- utility method
- semantic model name
- hybrid weights

That means if you run `exact_dp`, then later run `greedy_ratio` and `greedy_refine` with the same dataset and utility setup, the utility scores are reused instead of recomputed. Cache files are stored under `data/cache/`.

## 8) Metrics Computed

Per instance and budget:

- `selected_utility`
- `support_recall`
- `exact_support_coverage`
- `budget_utilization`
- `compression_ratio`
- `runtime_sec`
- `selected_chunks`
- `selected_cost_tokens`

Aggregated in `summary.csv` by `(merge_size, budget_tokens)`.

## 9) Utility Methods

- `lexical`:
  lightweight TF-IDF-style query/chunk relevance (default, no extra deps)
- `semantic`:
  embedding cosine similarity (requires `sentence-transformers`)
- `hybrid`:
  `alpha * semantic + beta * lexical`
  (falls back to lexical if semantic dependency is unavailable)

## 10) Notes for Class Project Use

- `distractor` split is used intentionally so gold evidence exists in context.
- Sentence chunking is implemented with period-based sub-splitting (`--chunking-mode period`).
- For fair comparisons, keep `--dp-cost-scale 1` so all algorithms use the same raw token costs.
- Only increase `--dp-cost-scale` if you explicitly want a faster approximate DP run.

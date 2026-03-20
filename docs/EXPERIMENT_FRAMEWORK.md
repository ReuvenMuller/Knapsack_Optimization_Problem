# Experimental Framework Specification

## Goal

Evaluate knapsack-based context compression algorithms under controlled scaling,
while preserving an NLP grounding via HotpotQA distractor data.

## Dataset Construction

Source dataset:
- `hotpotqa/hotpot_qa`
- config: `distractor`
- split: `validation` (recommended for reported results)

Merged-instance construction:
- keep exactly one target QA pair `(question, answer)`
- include its original context
- add context from `(k-1)` additional HotpotQA examples as distractors
- shuffle all chunks so target evidence is not contiguous

Default scaling plan:
- 20 samples at merge size 10
- 20 samples at merge size 20
- 20 samples at merge size 30
- 20 samples at merge size 40
- 20 samples at merge size 50

Total: 100 merged instances.

## Chunking

Chunking unit:
- sentence chunks

Implementation detail:
- each source sentence is split by period `"."`
- empty fragments are removed
- token cost is estimated using word/punctuation units

## Utility Computation

Supported utility methods:
- `lexical` (default):
  lightweight TF-IDF-style relevance between question and chunk
- `semantic`:
  sentence-embedding cosine similarity
- `hybrid`:
  weighted mix of semantic + lexical

For class reproducibility and low setup friction, `lexical` is the default.

## Algorithms

Compared solvers:
- `bruteforce`: exhaustive subset search (2^n), for tiny instances only
- `exact_dp`: exact 0/1 knapsack dynamic programming
- `greedy_ratio`: sort by utility/cost
- `greedy_refine`: greedy initialization plus local-search swaps/additions

## Correctness and Quality Evaluation

No LLM inference is required.

Primary correctness metrics:
- `support_recall`:
  selected gold-support chunks / total gold-support chunks
- `exact_support_coverage`:
  whether all gold-support chunks were retained

Additional metrics:
- selected utility
- budget utilization
- compression ratio
- runtime
- selected chunk count

## Runtime/Scaling Measurement

Track runtime by:
- merge size
- budget level
- algorithm

Expected trend:
- `exact_dp` highest cost as `n` and `B` grow
- `greedy_ratio` fastest baseline
- `greedy_refine` between exact DP and greedy ratio

## Reproducibility

Reproducibility controls:
- fixed seed for merged-instance generation
- merged dataset written to JSONL and reused for all algorithm runs
- per-run `run_config.json` stored with outputs

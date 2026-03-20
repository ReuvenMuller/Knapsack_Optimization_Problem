from __future__ import annotations

import argparse
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from knapsack_experiment.hotpot import (
    build_merged_instances,
    export_merged_jsonl,
    load_hotpotqa_examples,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build merged HotpotQA instances for knapsack compression experiments."
    )
    parser.add_argument("--source-config", default="distractor", help="HotpotQA config.")
    parser.add_argument("--source-split", default="validation", help="HotpotQA split.")
    parser.add_argument(
        "--merge-sizes",
        type=int,
        nargs="+",
        default=[10, 20, 30, 40, 50],
        help="Merged instance sizes.",
    )
    parser.add_argument(
        "--samples-per-size",
        type=int,
        default=20,
        help="How many merged instances to generate at each merge size.",
    )
    parser.add_argument(
        "--chunking-mode",
        choices=["period", "as_is"],
        default="period",
        help="Sentence chunking mode. 'period' splits each sentence by periods.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--output-path",
        default=os.path.join("data", "merged_hotpotqa_distractor_validation.jsonl"),
        help="Output JSONL path for merged instances.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    examples = load_hotpotqa_examples(config=args.source_config, split=args.source_split)
    merged = build_merged_instances(
        source_examples=examples,
        merge_sizes=args.merge_sizes,
        samples_per_size=args.samples_per_size,
        seed=args.seed,
        chunking_mode=args.chunking_mode,
        shuffle_chunks=True,
    )
    export_merged_jsonl(merged, args.output_path)

    print(f"Built {len(merged)} merged instances")
    print(f"Output: {args.output_path}")
    print(f"Merge sizes: {args.merge_sizes}")
    print(f"Samples per size: {args.samples_per_size}")
    print(f"Chunking mode: {args.chunking_mode}")


if __name__ == "__main__":
    main()

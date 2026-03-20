from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run all algorithms sequentially, each with its own output folder."
    )
    parser.add_argument("--dataset-path", required=True, help="Merged dataset JSONL path.")
    parser.add_argument(
        "--budgets",
        type=int,
        nargs="+",
        default=[2000, 4000, 8000],
        help="Token budgets.",
    )
    parser.add_argument(
        "--utility-method",
        choices=["lexical", "semantic", "hybrid"],
        default="lexical",
    )
    parser.add_argument("--results-dir", default="results")
    parser.add_argument(
        "--run-tag",
        default=None,
        help="Optional tag to append to per-algorithm run names.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    tag = args.run_tag or timestamp
    algorithms = ["exact_dp", "greedy_ratio", "greedy_refine"]

    for algo in algorithms:
        run_name = f"{tag}_{algo}"
        cmd = [
            sys.executable,
            os.path.join(ROOT_DIR, "scripts", "run_algorithm.py"),
            "--dataset-path",
            args.dataset_path,
            "--algorithm",
            algo,
            "--utility-method",
            args.utility_method,
            "--results-dir",
            args.results_dir,
            "--run-name",
            run_name,
            "--budgets",
            *[str(x) for x in args.budgets],
        ]
        print(f"Running {algo}...")
        subprocess.run(cmd, check=True)
    print("All algorithms completed.")


if __name__ == "__main__":
    main()

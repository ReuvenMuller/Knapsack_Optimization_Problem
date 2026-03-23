import csv
import os
import time

from build_merged_dataset import get_merged_instances
from algorithms import solve_exact_dp

# These are the budgets we will use for the knapsack problem.
# For simplicity we split by white spaces and take each word as a token.
BUDGETS = [2000, 4000, 8000]


# This function computes the metrics for the selection of chunks.
def compute_selection_metrics(selected_indices, costs, utilities, gold_support_flags, budget):
    total_cost = sum(costs)
    total_selected_cost = sum(costs[idx] for idx in selected_indices)
    total_selected_utility = sum(utilities[idx] for idx in selected_indices)

    gold_support_total = sum(1 for flag in gold_support_flags if flag)
    gold_support_selected = sum(
        1 for idx, is_support in enumerate(gold_support_flags) if is_support and idx in selected_indices
    )
    gold_support_recall = (
        float(gold_support_selected) / float(gold_support_total) if gold_support_total > 0 else 0.0
    )
    exact_gold_support_coverage = (
        1.0 if gold_support_total > 0 and gold_support_selected == gold_support_total else 0.0
    )

    return {
        "total_chunks": float(len(costs)),
        "total_cost_tokens": float(total_cost),
        "selected_chunks": float(len(selected_indices)),
        "total_selected_cost": float(total_selected_cost),
        "budget_utilization": float(total_selected_cost) / float(budget) if budget > 0 else 0.0,
        "compression_ratio": float(total_selected_cost) / float(total_cost) if total_cost > 0 else 0.0,
        "total_selected_utility": total_selected_utility,
        "gold_support_total": float(gold_support_total),
        "gold_support_selected": float(gold_support_selected),
        "gold_support_recall": gold_support_recall,
        "exact_gold_support_coverage": exact_gold_support_coverage,
    }


# This function writes the results to a CSV file.
def write_csv(path, rows):
    output_dir = os.path.dirname(path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    if not rows:
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write("")
        return

    columns = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

# This function runs the experiment for the given instances.
# Later add args for specific algorithms.
def run_algorithm_experiment(merged_instances):
    instances = merged_instances

    records = []
    current_merge_size = None

    for instance in instances:
        if instance["merge_size"] != current_merge_size:
            current_merge_size = instance["merge_size"]
            print(f"Running merge size {current_merge_size}...")

        raw_costs = []
        utilities = []
        support_flags = []

        for paragraph in instance["context"]:
            for chunk in paragraph["chunks"]:
                raw_costs.append(int(chunk["chunk_size"]))
                utilities.append(float(chunk["chunk_utility"]))
                support_flags.append(bool(chunk["gold_answer"]))

        for budget in BUDGETS:
            started = time.perf_counter()
            selected_indices = solve_exact_dp(raw_costs, utilities, budget)
            runtime_sec = time.perf_counter() - started
        
        # Later we will modify the code here to include the remaing algorithms
            metrics = compute_selection_metrics(
                selected_indices=selected_indices,
                costs=raw_costs,
                utilities=utilities,
                gold_support_flags=support_flags,
                budget=budget,
            )

            records.append(
                {
                    "algorithm": "exact_dp",
                    "merged_id": instance["merged_id"],
                    "merge_size": instance["merge_size"],
                    "target_example_id": instance["target_example_id"],
                    "budget_tokens": budget,
                    "runtime_sec": runtime_sec,
                    **metrics,
                }
            )
        print(f"Completed run for token budget {budget}.")
    return records


def main():
    # First we build and merge the dataset.
    merged_instances = get_merged_instances()

    # Then we run the experiment for the given instances.
    records = run_algorithm_experiment(merged_instances)

    # Finally we write the results to a CSV file.
    write_csv("results.csv", records)

    print("Algorithm run complete: exact_dp")
    print(f"Instances processed: {len(merged_instances)}")
    print(f"Detail results: results.csv")


if __name__ == "__main__":
    main()

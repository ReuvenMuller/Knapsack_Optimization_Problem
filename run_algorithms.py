import csv
import os
import time

from build_merged_dataset import get_merged_instances
from algorithms import solve_exact_dp, solve_greedy_ratio, solve_greedy_refine

# These are the budgets we will use for the knapsack problem.
# For simplicity we split by white spaces and take each word as a token.
BUDGETS = [2000, 4000, 8000]
TIMING_REPEATS = {
    "exact_dp": 1,
    "greedy_ratio": 10,
    "greedy_refine": 10,
}

ALGORITHMS = [
    ("exact_dp", solve_exact_dp),
    ("greedy_ratio", solve_greedy_ratio),
    ("greedy_refine", solve_greedy_refine),
]


# This function computes the metrics for the selection of chunks.
def compute_selection_metrics(selected_indices, costs, utilities, gold_support_flags, budget):
    total_cost = sum(costs)
    total_selected_cost = sum(costs[idx] for idx in selected_indices)
    total_selected_utility = sum(utilities[idx] for idx in selected_indices)
    selected_set = set(selected_indices)

    gold_support_total = sum(1 for flag in gold_support_flags if flag)
    gold_support_selected = sum(
        1 for idx, is_support in enumerate(gold_support_flags) if is_support and idx in selected_set
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


# This function runs a solver several times and returns the median runtime.
# The greedy algorithms are very fast, so one timing can be noisy.
def time_solver(solver, costs, utilities, budget, repeats):
    runtimes = []
    selected_indices = []

    for _ in range(repeats):
        started = time.perf_counter()
        selected_indices = solver(costs, utilities, budget)
        runtimes.append(time.perf_counter() - started)

    runtimes.sort()
    middle = len(runtimes) // 2
    median_runtime = runtimes[middle]

    return selected_indices, median_runtime


# This function runs the experiment for the given instances.
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
            budget_results = {}

            # Run Exact-DP first because it is the optimal baseline.
            exact_selected, exact_runtime_sec = time_solver(
                solve_exact_dp,
                raw_costs,
                utilities,
                budget,
                TIMING_REPEATS["exact_dp"],
            )

            exact_metrics = compute_selection_metrics(
                selected_indices=exact_selected,
                costs=raw_costs,
                utilities=utilities,
                gold_support_flags=support_flags,
                budget=budget,
            )
            budget_results["exact_dp"] = (exact_selected, exact_runtime_sec, exact_metrics)

            # Run the two heuristic algorithms on the same instance and budget.
            for algorithm_name, solver in ALGORITHMS[1:]:
                selected_indices, runtime_sec = time_solver(
                    solver,
                    raw_costs,
                    utilities,
                    budget,
                    TIMING_REPEATS[algorithm_name],
                )

                metrics = compute_selection_metrics(
                    selected_indices=selected_indices,
                    costs=raw_costs,
                    utilities=utilities,
                    gold_support_flags=support_flags,
                    budget=budget,
                )
                budget_results[algorithm_name] = (selected_indices, runtime_sec, metrics)

            exact_utility = exact_metrics["total_selected_utility"]

            for algorithm_name, _ in ALGORITHMS:
                selected_indices, runtime_sec, metrics = budget_results[algorithm_name]
                if algorithm_name == "exact_dp":
                    relative_utility_to_exact = 1.0
                elif exact_utility > 0:
                    relative_utility_to_exact = metrics["total_selected_utility"] / exact_utility
                else:
                    relative_utility_to_exact = 0.0

                records.append(
                    {
                        "algorithm": algorithm_name,
                        "merged_id": instance["merged_id"],
                        "merge_size": instance["merge_size"],
                        "target_example_id": instance["target_example_id"],
                        "budget_tokens": budget,
                        "timing_repeats": TIMING_REPEATS[algorithm_name],
                        "runtime_sec": runtime_sec,
                        "relative_utility_to_exact": relative_utility_to_exact,
                        **metrics,
                    }
                )

            print(f"Completed run for token budget {budget}.")

        print(f"Completed merge instance {instance['merged_id']}.")
    return records


def main():
    # First we build and merge the dataset.
    merged_instances = get_merged_instances()

    # Then we run the experiment for the given instances.
    records = run_algorithm_experiment(merged_instances)

    # Finally we write the results to a CSV file.
    write_csv("results.csv", records)

    print("Algorithm run complete: exact_dp, greedy_ratio, greedy_refine")
    print(f"Instances processed: {len(merged_instances)}")
    print(f"Detail results: results.csv")


if __name__ == "__main__":
    main()

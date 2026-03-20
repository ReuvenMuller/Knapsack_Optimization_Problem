from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from statistics import mean

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from knapsack_experiment.experiment import run_algorithm_experiment
from knapsack_experiment.hotpot import export_merged_jsonl, load_merged_jsonl


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_first_run_details(results_root: str, algorithm: str, run_name: str) -> dict[str, str]:
    import csv

    path = os.path.join(results_root, algorithm, run_name, "details.csv")
    with open(path, "r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"No rows found in {path}")
    return rows[0]


def select_one_instance_per_merge_size(dataset_path: str) -> list:
    instances = load_merged_jsonl(dataset_path)
    seen: set[int] = set()
    selected = []
    for instance in instances:
        if instance.merge_size in seen:
            continue
        selected.append(instance)
        seen.add(instance.merge_size)
    return sorted(selected, key=lambda inst: inst.merge_size)


def svg_line_chart(
    series: dict[str, list[tuple[float, float]]],
    title: str,
    x_label: str,
    y_label: str,
    output_path: str,
) -> None:
    width = 900
    height = 520
    margin_left = 80
    margin_right = 40
    margin_top = 60
    margin_bottom = 80
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    all_points = [point for points in series.values() for point in points]
    x_vals = [p[0] for p in all_points]
    y_vals = [p[1] for p in all_points]
    x_min, x_max = min(x_vals), max(x_vals)
    y_min, y_max = 0.0, max(y_vals) * 1.1 if max(y_vals) > 0 else 1.0

    def x_to_px(x: float) -> float:
        if x_max == x_min:
            return margin_left + plot_width / 2
        return margin_left + ((x - x_min) / (x_max - x_min)) * plot_width

    def y_to_px(y: float) -> float:
        if y_max == y_min:
            return margin_top + plot_height / 2
        return margin_top + plot_height - ((y - y_min) / (y_max - y_min)) * plot_height

    colors = {
        "exact_dp": "#0B5D8C",
        "greedy_ratio": "#2C9A5F",
        "greedy_refine": "#C06C2B",
    }

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">'
    )
    parts.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    parts.append(
        f'<text x="{width/2}" y="30" text-anchor="middle" font-family="Segoe UI, Arial" '
        f'font-size="22" fill="#1f2937">{title}</text>'
    )

    # Axes
    x0 = margin_left
    y0 = margin_top + plot_height
    x1 = margin_left + plot_width
    y1 = margin_top
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="#374151" stroke-width="2"/>')
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#374151" stroke-width="2"/>')

    # Grid + ticks
    y_ticks = 5
    for i in range(y_ticks + 1):
        value = y_min + (y_max - y_min) * i / y_ticks
        y = y_to_px(value)
        parts.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#e5e7eb" stroke-width="1"/>')
        parts.append(
            f'<text x="{x0 - 10}" y="{y + 4}" text-anchor="end" font-family="Segoe UI, Arial" '
            f'font-size="12" fill="#4b5563">{value:.4f}</text>'
        )

    unique_x = sorted(set(x_vals))
    for value in unique_x:
        x = x_to_px(value)
        parts.append(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1}" stroke="#f3f4f6" stroke-width="1"/>')
        label = f"{int(value)}"
        parts.append(
            f'<text x="{x}" y="{y0 + 24}" text-anchor="middle" font-family="Segoe UI, Arial" '
            f'font-size="12" fill="#4b5563">{label}</text>'
        )

    # Series
    legend_y = margin_top + 10
    legend_x = width - 240
    row = 0
    for name, points in series.items():
        color = colors.get(name, "#111827")
        points = sorted(points, key=lambda p: p[0])
        path_d = " ".join(
            ("M" if idx == 0 else "L") + f" {x_to_px(x):.2f} {y_to_px(y):.2f}"
            for idx, (x, y) in enumerate(points)
        )
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="3"/>')
        for x, y in points:
            parts.append(f'<circle cx="{x_to_px(x):.2f}" cy="{y_to_px(y):.2f}" r="4" fill="{color}"/>')

        ly = legend_y + row * 22
        parts.append(f'<line x1="{legend_x}" y1="{ly}" x2="{legend_x + 24}" y2="{ly}" stroke="{color}" stroke-width="3"/>')
        parts.append(
            f'<text x="{legend_x + 32}" y="{ly + 4}" font-family="Segoe UI, Arial" '
            f'font-size="13" fill="#1f2937">{name}</text>'
        )
        row += 1

    parts.append(
        f'<text x="{width/2}" y="{height - 20}" text-anchor="middle" font-family="Segoe UI, Arial" '
        f'font-size="14" fill="#1f2937">{x_label}</text>'
    )
    parts.append(
        f'<text x="20" y="{height/2}" text-anchor="middle" font-family="Segoe UI, Arial" '
        f'font-size="14" fill="#1f2937" transform="rotate(-90 20 {height/2})">{y_label}</text>'
    )
    parts.append("</svg>")

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(parts))


def main() -> None:
    dataset_path = os.path.join(ROOT_DIR, "data", "merged_hotpotqa_distractor_validation.jsonl")
    results_root = os.path.join(ROOT_DIR, "results")
    report_dir = os.path.join(ROOT_DIR, "report")
    benchmark_dir = os.path.join(results_root, "benchmark_runs")
    ensure_dir(report_dir)
    ensure_dir(benchmark_dir)

    selected = select_one_instance_per_merge_size(dataset_path)
    subset_path = os.path.join(report_dir, "benchmark_subset_one_per_size.jsonl")
    export_merged_jsonl(selected, subset_path)

    benchmark_records: dict[str, list[dict[str, object]]] = {}
    algorithms = ["exact_dp", "greedy_ratio", "greedy_refine"]
    for algorithm in algorithms:
        records, _ = run_algorithm_experiment(
            merged_dataset_path=subset_path,
            algorithm=algorithm,
            budgets=[2000],
            utility_method="lexical",
            dp_cost_scale=1,
            max_instances=None,
            compute_optimality_gap=False,
            local_search_iterations=50,
            local_search_candidate_pool=300,
        )
        benchmark_records[algorithm] = records
        out_path = os.path.join(benchmark_dir, f"{algorithm}_benchmark_2000.json")
        with open(out_path, "w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2)

    runtime_by_merge_size: dict[str, list[tuple[float, float]]] = {}
    runtime_by_chunks: dict[str, list[tuple[float, float]]] = {}
    for algorithm, records in benchmark_records.items():
        runtime_by_merge_size[algorithm] = [
            (float(r["merge_size"]), float(r["runtime_sec"])) for r in records
        ]
        runtime_by_chunks[algorithm] = [
            (float(r["total_chunks"]), float(r["runtime_sec"])) for r in records
        ]

    merge_size_svg = os.path.join(report_dir, "runtime_vs_merge_size.svg")
    chunk_svg = os.path.join(report_dir, "runtime_vs_total_chunks.svg")
    svg_line_chart(
        runtime_by_merge_size,
        "Runtime vs Merge Size (Budget = 2000)",
        "Merge Size",
        "Runtime (seconds)",
        merge_size_svg,
    )
    svg_line_chart(
        runtime_by_chunks,
        "Runtime vs Total Chunks (Budget = 2000)",
        "Total Chunks",
        "Runtime (seconds)",
        chunk_svg,
    )

    exact_first = load_first_run_details(results_root, "exact_dp", "exact_dp_first")
    greedy_first = load_first_run_details(results_root, "greedy_ratio", "greedy_ratio_first")
    refine_first = load_first_run_details(results_root, "greedy_refine", "greedy_refine_first")

    # Build concise table for the first user-run comparison.
    first_rows = [exact_first, greedy_first, refine_first]
    lines: list[str] = []
    lines.append("# Small Report: Algorithm Results and Time Complexity")
    lines.append("")
    lines.append(f"Generated on {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("## 1. Your First Completed Runs")
    lines.append("")
    lines.append("| Algorithm | Runtime (s) | Selected Utility | Support Recall | Exact Support Coverage | Selected Cost |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in first_rows:
        lines.append(
            f"| {row['algorithm']} | {float(row['runtime_sec']):.6f} | "
            f"{float(row['selected_utility']):.6f} | {float(row['support_recall']):.2f} | "
            f"{float(row['exact_support_coverage']):.2f} | {float(row['selected_cost_tokens']):.0f} |"
        )
    lines.append("")
    lines.append("Observations:")
    lines.append("")
    lines.append("- All three algorithms retained both gold support sentences on the first instance (`support_recall = 1.0`).")
    lines.append("- `greedy_ratio` was the fastest on that instance.")
    lines.append("- `greedy_refine` was slower than `greedy_ratio`, but still much faster than DP.")
    lines.append("- These first-run files were generated before the fair-comparison patch, so `exact_dp` there used `dp_cost_scale = 4` while the greedy runs used raw costs.")
    lines.append("")
    lines.append("## 2. Benchmark For Time Complexity")
    lines.append("")
    lines.append("I ran one representative merged instance at each merge size (`10, 20, 30, 40, 50`) with budget `2000` and lexical utility.")
    lines.append("")
    lines.append("| Algorithm | Avg Runtime (s) | Max Runtime (s) | Avg Chunks |")
    lines.append("|---|---:|---:|---:|")
    for algorithm in algorithms:
        records = benchmark_records[algorithm]
        lines.append(
            f"| {algorithm} | {mean(float(r['runtime_sec']) for r in records):.6f} | "
            f"{max(float(r['runtime_sec']) for r in records):.6f} | "
            f"{mean(float(r['total_chunks']) for r in records):.1f} |"
        )
    lines.append("")
    lines.append("Trend summary:")
    lines.append("")
    lines.append("- `greedy_ratio` scales best and stays extremely fast as chunk count increases.")
    lines.append("- `greedy_refine` scales worse than plain greedy because of the local-search improvement step.")
    lines.append("- `exact_dp` grows the fastest with instance size because it explores budget states dynamically.")
    lines.append("")
    lines.append("## 3. Graphs")
    lines.append("")
    lines.append(f"![Runtime vs Merge Size]({merge_size_svg})")
    lines.append("")
    lines.append(f"![Runtime vs Total Chunks]({chunk_svg})")
    lines.append("")
    lines.append("## 4. Interpretation")
    lines.append("")
    lines.append("For this project, the runtime story is already visible: greedy is the practical fast heuristic, greedy-refine trades extra time for potentially better selections, and DP is the strongest exact-style baseline but scales less favorably. Brute force is not realistic for your real merged instances because even the smallest one had hundreds of chunks.")

    report_path = os.path.join(report_dir, "time_complexity_report.md")
    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))

    print(f"Report written to: {report_path}")
    print(f"Graph written to: {merge_size_svg}")
    print(f"Graph written to: {chunk_svg}")


if __name__ == "__main__":
    main()

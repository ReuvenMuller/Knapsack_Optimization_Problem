from __future__ import annotations

import csv
import os
import sys
from datetime import datetime, timezone

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_DIR = os.path.join(ROOT_DIR, "report")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def read_summary(path: str) -> list[dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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
    y_min = 0.0
    y_max = max(y_vals) * 1.15 if max(y_vals) > 0 else 1.0

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
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    )
    parts.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    parts.append(
        f'<text x="{width/2}" y="30" text-anchor="middle" font-family="Segoe UI, Arial" font-size="22" fill="#1f2937">{title}</text>'
    )

    x0 = margin_left
    y0 = margin_top + plot_height
    x1 = margin_left + plot_width
    y1 = margin_top
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="#374151" stroke-width="2"/>')
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="#374151" stroke-width="2"/>')

    for i in range(6):
        value = y_min + (y_max - y_min) * i / 5
        y = y_to_px(value)
        parts.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#e5e7eb" stroke-width="1"/>')
        parts.append(
            f'<text x="{x0 - 10}" y="{y + 4}" text-anchor="end" font-family="Segoe UI, Arial" font-size="12" fill="#4b5563">{value:.3f}</text>'
        )

    for value in sorted(set(x_vals)):
        x = x_to_px(value)
        parts.append(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1}" stroke="#f3f4f6" stroke-width="1"/>')
        parts.append(
            f'<text x="{x}" y="{y0 + 24}" text-anchor="middle" font-family="Segoe UI, Arial" font-size="12" fill="#4b5563">{int(value)}</text>'
        )

    legend_x = width - 230
    legend_y = margin_top + 10
    for row, (name, points) in enumerate(series.items()):
        color = colors.get(name, "#111827")
        sorted_points = sorted(points, key=lambda p: p[0])
        path_d = " ".join(
            ("M" if idx == 0 else "L") + f" {x_to_px(x):.2f} {y_to_px(y):.2f}"
            for idx, (x, y) in enumerate(sorted_points)
        )
        parts.append(f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="3"/>')
        for x, y in sorted_points:
            parts.append(f'<circle cx="{x_to_px(x):.2f}" cy="{y_to_px(y):.2f}" r="4" fill="{color}"/>')

        ly = legend_y + row * 22
        parts.append(f'<line x1="{legend_x}" y1="{ly}" x2="{legend_x + 24}" y2="{ly}" stroke="{color}" stroke-width="3"/>')
        parts.append(
            f'<text x="{legend_x + 32}" y="{ly + 4}" font-family="Segoe UI, Arial" font-size="13" fill="#1f2937">{name}</text>'
        )

    parts.append(
        f'<text x="{width/2}" y="{height - 20}" text-anchor="middle" font-family="Segoe UI, Arial" font-size="14" fill="#1f2937">{x_label}</text>'
    )
    parts.append(
        f'<text x="20" y="{height/2}" text-anchor="middle" font-family="Segoe UI, Arial" font-size="14" fill="#1f2937" transform="rotate(-90 20 {height/2})">{y_label}</text>'
    )
    parts.append("</svg>")

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(parts))


def main() -> None:
    ensure_dir(REPORT_DIR)

    exact_rows = read_summary(os.path.join(ROOT_DIR, "results", "exact_dp", "fresh_full_exact_dp", "summary.csv"))
    greedy_rows = read_summary(os.path.join(ROOT_DIR, "results", "greedy_ratio", "fresh_full_greedy_ratio", "summary.csv"))
    refine_rows = read_summary(os.path.join(ROOT_DIR, "results", "greedy_refine", "fresh_full_greedy_refine", "summary.csv"))

    rows_by_algo = {
        "exact_dp": exact_rows,
        "greedy_ratio": greedy_rows,
        "greedy_refine": refine_rows,
    }

    graph_paths: list[str] = []
    for budget in (2000, 4000, 8000):
        series: dict[str, list[tuple[float, float]]] = {}
        for algo, rows in rows_by_algo.items():
            series[algo] = [
                (float(row["merge_size"]), float(row["avg_runtime_sec"]))
                for row in rows
                if int(row["budget_tokens"]) == budget
            ]
        out_path = os.path.join(REPORT_DIR, f"runtime_vs_merge_size_budget_{budget}.svg")
        graph_paths.append(out_path)
        svg_line_chart(
            series,
            f"Runtime vs Merge Size (Budget = {budget})",
            "Merge Size",
            "Average Runtime (seconds)",
            out_path,
        )

    dp_50_8000 = next(
        row for row in exact_rows if int(row["merge_size"]) == 50 and int(row["budget_tokens"]) == 8000
    )
    greedy_50_8000 = next(
        row for row in greedy_rows if int(row["merge_size"]) == 50 and int(row["budget_tokens"]) == 8000
    )
    refine_50_8000 = next(
        row for row in refine_rows if int(row["merge_size"]) == 50 and int(row["budget_tokens"]) == 8000
    )
    speedup_greedy = float(dp_50_8000["avg_runtime_sec"]) / float(greedy_50_8000["avg_runtime_sec"])
    speedup_refine = float(dp_50_8000["avg_runtime_sec"]) / float(refine_50_8000["avg_runtime_sec"])

    report_path = os.path.join(REPORT_DIR, "full_experiment_report.md")
    lines: list[str] = []
    lines.append("# Full Experiment Report")
    lines.append("")
    lines.append(f"Generated on {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("## Setup")
    lines.append("")
    lines.append("- Dataset: merged HotpotQA distractor validation set")
    lines.append("- Total merged instances: 100")
    lines.append("- Merge sizes: 10, 20, 30, 40, 50")
    lines.append("- Budgets: 2000, 4000, 8000")
    lines.append("- Algorithms: exact_dp, greedy_ratio, greedy_refine")
    lines.append("- Utility method: lexical")
    lines.append("- Fair comparison: all methods used raw token costs (`dp_cost_scale = 1`)")
    lines.append("")
    lines.append("## Key Findings")
    lines.append("")
    lines.append(
        f"- At the hardest reported setting (`merge_size = 50`, `budget = 8000`), `exact_dp` averaged {float(dp_50_8000['avg_runtime_sec']):.4f}s, "
        f"`greedy_ratio` averaged {float(greedy_50_8000['avg_runtime_sec']):.4f}s, and `greedy_refine` averaged {float(refine_50_8000['avg_runtime_sec']):.4f}s."
    )
    lines.append(
        f"- In that setting, `greedy_ratio` was about {speedup_greedy:.0f}x faster than `exact_dp`, and `greedy_refine` was about {speedup_refine:.0f}x faster."
    )
    lines.append("- As budget increased from 2000 to 8000, runtime increased sharply for `exact_dp`, but only modestly for the greedy methods.")
    lines.append("- `greedy_ratio` and `greedy_refine` had nearly identical utility/correctness summaries in these runs, which suggests the current local-search refinement often did not improve over the greedy starting solution.")
    lines.append("- Support recall generally improved as the budget increased, across all methods.")
    lines.append("")
    lines.append("## Runtime Graphs")
    lines.append("")
    for path in graph_paths:
        lines.append(f"![{os.path.basename(path)}]({path})")
        lines.append("")
    lines.append("## Summary Tables")
    lines.append("")
    lines.append("### exact_dp")
    lines.append("")
    lines.append(f"[summary.csv]({os.path.join(ROOT_DIR, 'results', 'exact_dp', 'fresh_full_exact_dp', 'summary.csv')})")
    lines.append("")
    lines.append("### greedy_ratio")
    lines.append("")
    lines.append(f"[summary.csv]({os.path.join(ROOT_DIR, 'results', 'greedy_ratio', 'fresh_full_greedy_ratio', 'summary.csv')})")
    lines.append("")
    lines.append("### greedy_refine")
    lines.append("")
    lines.append(f"[summary.csv]({os.path.join(ROOT_DIR, 'results', 'greedy_refine', 'fresh_full_greedy_refine', 'summary.csv')})")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The runtime story is clean and matches the algorithmic intuition for this project. `exact_dp` gives the strongest exact baseline but scales worst as merge size and budget grow. `greedy_ratio` is extremely fast and appears to preserve most of the useful behavior at a tiny fraction of the runtime. `greedy_refine` adds extra computation over plain greedy, but under the current refinement strategy it did not materially improve the aggregate quality metrics in the full run.")

    with open(report_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))

    print(f"Report written to: {report_path}")
    for path in graph_paths:
        print(f"Graph written to: {path}")


if __name__ == "__main__":
    main()

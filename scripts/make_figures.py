#!/usr/bin/env python
# coding=utf-8
"""Generate the two figures used in REPORT.md from raw result jsonl files.

Usage:
    python make_figures.py <xbench_output_dir> <output_dir>
"""
import json
import os
import sys

import matplotlib.pyplot as plt

# (file, label, color, label offset in fig.1)
SETTINGS = [
    ("nomem_20.jsonl", "No-Memory", "tab:gray", (-12, -18)),
    ("lightweight_20.jsonl", "Lightweight\n(MemEvolve)", "tab:green", (-60, 12)),
    ("expel_20.jsonl", "ExpeL", "tab:orange", (8, -4)),
    ("voyager_20.jsonl", "Voyager", "tab:blue", (8, 6)),
    ("lightweight_gated_20.jsonl", "Lightweight\n+ Gating", "tab:red", (-95, -4)),
]
TASK10_ID = "10"


def load(path):
    rows = {}
    with open(path) as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                rows[str(r["task_id"])] = r  # last record wins on rerun
    return rows


def main(data_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    stats = []
    for fname, label, color, offset in SETTINGS:
        rows = load(os.path.join(data_dir, fname))
        n = len(rows)
        acc = sum(r["score"] for r in rows.values()) / n * 100
        tok = sum(r["metrics"]["total_tokens"] for r in rows.values()) / n
        t10 = rows.get(TASK10_ID)
        stats.append({
            "label": label, "color": color, "offset": offset, "acc": acc, "tok": tok,
            "t10_tok": t10["metrics"]["total_tokens"], "t10_ok": t10["score"] == 1,
        })

    # Figure 1: accuracy vs avg token per task
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    for s in stats:
        ax.scatter(s["tok"] / 1000, s["acc"], s=140, color=s["color"], zorder=3)
        ax.annotate(s["label"].replace("\n", " "), (s["tok"] / 1000, s["acc"]),
                    textcoords="offset points", xytext=s["offset"], fontsize=9)
    ax.set_xlabel("Avg tokens per task (k)")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Accuracy vs. cost on xBench-DS (first 20 tasks)")
    ax.set_ylim(70, 95)
    ax.grid(alpha=0.3, zorder=0)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "accuracy_vs_cost.png"), dpi=150)

    # Figure 2: token consumption on task 10
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    labels = [s["label"] for s in stats]
    tokens = [s["t10_tok"] / 1e6 for s in stats]
    colors = ["tab:green" if s["t10_ok"] else "tab:red" for s in stats]
    bars = ax.bar(labels, tokens, color=colors, zorder=3)
    for bar, s in zip(bars, stats):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                ("correct" if s["t10_ok"] else "wrong"), ha="center", fontsize=9)
    ax.set_ylabel("Tokens (millions)")
    ax.set_title("Task 10 (equidistant-point geometry): token consumption")
    ax.grid(axis="y", alpha=0.3, zorder=0)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "task10_tokens.png"), dpi=150)
    print("saved 2 figures to", out_dir)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

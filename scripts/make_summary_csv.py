#!/usr/bin/env python
# coding=utf-8
"""Build a plaintext-free per-task summary CSV from raw result jsonl files.

Emits only non-sensitive metrics (no question/answer text), so it is safe to
commit to a public repo while xBench plaintext stays offline. Supports the
report's tables, figures, and per-task o/x grid.

Usage:
    python make_summary_csv.py <xbench_output_dir> <out_csv>
"""
import csv
import json
import os
import sys

# (filename, setting label)
GROUPS = [
    ("nomem_20.jsonl", "no-memory"),
    ("lightweight_20.jsonl", "lightweight"),
    ("expel_20.jsonl", "expel"),
    ("voyager_20.jsonl", "voyager"),
    ("lightweight_gated_20.jsonl", "lightweight-gated"),
]
FIELDS = ["setting", "task_id", "score", "total_tokens", "prompt_tokens",
          "completion_tokens", "api_calls", "elapsed_time",
          "memory_injected", "injection_steps", "agent_steps"]


def load(path):
    rows = {}
    with open(path) as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                rows[str(r["task_id"])] = r  # last record wins on rerun
    return rows


def main(data_dir, out_csv):
    out_rows = []
    for fname, setting in GROUPS:
        path = os.path.join(data_dir, fname)
        if not os.path.exists(path):
            print(f"skip (missing): {fname}")
            continue
        for tid, r in load(path).items():
            traj = r.get("agent_trajectory", [])
            inj = sum(1 for s in traj if s.get("memory_guidance"))
            m = r.get("metrics", {})
            out_rows.append({
                "setting": setting,
                "task_id": tid,
                "score": r.get("score"),
                "total_tokens": m.get("total_tokens"),
                "prompt_tokens": m.get("prompt_tokens"),
                "completion_tokens": m.get("completion_tokens"),
                "api_calls": m.get("api_calls"),
                "elapsed_time": round(m.get("elapsed_time", 0), 1),
                "memory_injected": int(inj > 0),
                "injection_steps": inj,
                "agent_steps": len(traj),
            })
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out_rows)
    print(f"wrote {len(out_rows)} rows to {out_csv}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])

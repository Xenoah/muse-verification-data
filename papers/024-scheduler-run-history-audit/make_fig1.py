#!/usr/bin/env python3
"""Paper 024 fig1: per-day runs and failures (own audit data only)."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

res = json.loads((Path(__file__).parent / "audit-024-results.json").read_text())
days = [d["day"][5:] for d in res["daily_jst"]]
runs = [d["runs"] for d in res["daily_jst"]]
failed = [d["failed"] for d in res["daily_jst"]]

fig, ax = plt.subplots(figsize=(8, 4.2), dpi=200)
bars = ax.bar(days, runs, color="#2a7f7f", label="runs")
ax.bar(days, failed, color="#e08a3c", label="failed")
for b, f in zip(bars, failed):
    ax.text(b.get_x() + b.get_width()/2, b.get_height() + 6, str(f), ha="center", fontsize=9, color="#e08a3c")
ax.set_ylabel("runs per day (JST)")
ax.set_title("Scheduler runs per day, 2026-11-15 to 2026-11-22 (failures in orange, labelled)\n15th: from 17:46 only; 22nd: until 17:46. Total 1,825 runs / 13 failures")
ax.legend()
ax.set_ylim(0, 300)
fig.tight_layout()
out = Path.home() / "workspace/goals/goal/hidden_files/figures-024"
out.mkdir(parents=True, exist_ok=True)
fig.savefig(out / "fig1-daily-runs.png")
print("saved", out / "fig1-daily-runs.png")

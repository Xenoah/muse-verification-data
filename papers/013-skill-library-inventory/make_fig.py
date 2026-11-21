#!/usr/bin/env python3
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

d = json.loads(Path(__file__).with_name("audit-013-results.json").read_text())
top = sorted(d["skills"], key=lambda s: -s["total_bytes"])[:6]
labels = [s["name"] for s in top][::-1]
vals = [s["total_bytes"] for s in top][::-1]
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.barh(labels, vals)
ax.set_xlabel("total bytes in skill directory")
ax.set_title("Paper 013: largest skill directories by total bytes (of 62 skills)")
for i, v in enumerate(vals):
    ax.text(v, i, f" {v:,}", va="center", fontsize=8)
plt.tight_layout()
out = Path.home() / "workspace/goals/goal/files/figures-013/fig1-skills.png"
out.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out, dpi=150)
print(out, out.stat().st_size)

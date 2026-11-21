#!/usr/bin/env python3
"""Figure for paper 014 from audit-014-results.json only."""
import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
d = json.loads((Path(__file__).parent / "audit-014-results.json").read_text())
per = sorted(d["per_goal"], key=lambda f: -f["total_bytes"])[:6]
labels = [f["slug"] for f in per]
vals = [f["total_bytes"] for f in per]
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].barh(labels[::-1], vals[::-1], color="#4C78A8")
axes[0].set_title("Top goal workspaces by bytes")
axes[0].set_xlabel("bytes")
tr = d["tracking"]
axes[1].bar(["tracking\nactive", "tracking\ncompleted", "user goals\nactive"], [tr["active"], tr["completed"], d["usergoals"]["active"]], color=["#54A24B", "#B279A2", "#F58518"])
axes[1].set_title("Roster counts by surface / status")
axes[1].set_ylabel("items")
for i, v in enumerate([tr["active"], tr["completed"], d["usergoals"]["active"]]):
    axes[1].text(i, v + 0.4, str(v), ha="center")
plt.tight_layout()
out = Path.home() / "workspace/goals/goal/files/figures-014/fig1-goals.png"
plt.savefig(out, dpi=150)
print(out, out.stat().st_size)

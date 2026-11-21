#!/usr/bin/env python3
"""Figure for paper 015 from audit-015-results.json only."""
import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
d = json.loads((Path(__file__).parent / "audit-015-results.json").read_text())
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
kinds = ["CONNECTOR.md\n(main docs)", "references/\n(extra docs)", "manifest.yaml", "connector.yaml", "scripts"]
vals = [697229, 392936, 483236, 43362, 16631]
axes[0].bar(kinds, vals, color=["#4C78A8", "#54A24B", "#F58518", "#B279A2", "#72B7B2"])
axes[0].set_title("Total bytes by file kind (111 connectors)")
axes[0].set_ylabel("bytes")
axes[0].tick_params(axis="x", labelsize=7)
top5 = d["per_connector_total_bytes"]["top5"]
axes[1].barh([t["name"] for t in top5][::-1], [t["bytes"] for t in top5][::-1], color="#4C78A8")
axes[1].set_title("Top 5 connectors by total bytes")
axes[1].set_xlabel("bytes")
plt.tight_layout()
out = Path(__file__).parent / "figures-015" / "fig1-connectors.png"
plt.savefig(out, dpi=150)
print(out, out.stat().st_size)

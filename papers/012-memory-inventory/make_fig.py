import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
base = pathlib.Path.home() / "workspace/goals/goal/hidden_files/audit-012"
res = json.loads((base / "audit-012-results.json").read_text())
cats = res["categories"]
order = ["bank", "daily", "curated", "people", "groups", "shopping"]
labels = {"bank": "bank (derived)", "daily": "daily logs", "curated": "MEMORY.md",
          "people": "people", "groups": "groups", "shopping": "shopping"}
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
axes[0].barh([labels[k] for k in order][::-1],
             [cats[k]["bytes"] / 1000 for k in order][::-1], color="#4a7ebb")
axes[0].set_title("Memory store by category (bytes)")
axes[0].set_xlabel("KB")
detail = res["daily"]["detail"]
axes[1].bar([d["date"][5:] for d in detail],
            [d["bytes"] / 1000 for d in detail], color="#5a9e6f")
axes[1].set_title("Daily log size by date (24 days, no gaps)")
axes[1].set_ylabel("KB")
axes[1].tick_params(axis="x", labelrotation=90, labelsize=7)
plt.tight_layout()
out = pathlib.Path.home() / "workspace/goals/goal/files/figures-012/fig1-memory.png"
out.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out, dpi=150)
print(out, out.stat().st_size)

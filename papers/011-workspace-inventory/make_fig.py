import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
base = pathlib.Path.home() / "workspace/goals/goal/hidden_files/audit-011"
res = json.loads((base / "audit-011-results.json").read_text())
top = res["per_top_level"]
by_bytes = top[:8]
by_files = sorted(top, key=lambda d: -d["files"])[:8]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
axes[0].barh([d["name"] for d in by_bytes][::-1],
             [d["bytes"] / 1e9 for d in by_bytes][::-1], color="#4a7ebb")
axes[0].set_title("Top-level entries by bytes")
axes[0].set_xlabel("GB (logical size)")
axes[1].barh([d["name"] for d in by_files][::-1],
             [d["files"] for d in by_files][::-1], color="#5a9e6f")
axes[1].set_title("Top-level entries by file count")
axes[1].set_xlabel("files")
plt.tight_layout()
out = pathlib.Path.home() / "workspace/goals/goal/files/figures-011/fig1-workspace.png"
out.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(out, dpi=150)
print(out, out.stat().st_size)

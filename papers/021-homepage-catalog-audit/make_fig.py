import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Noto Sans CJK JP"
base = os.path.expanduser("~/workspace/goals/goal/hidden_files/audit-021")
o = json.load(open(os.path.join(base, "audit-021-results.json")))
fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), dpi=200)
# Left: per-category pages present vs source-only
cats_present = dict(o["pages_present_by_category"])
cats_null = dict(o["pages_null_by_category"])
order = [c for c, _ in o["categories"]]
labels = order
present = [cats_present.get(c, 0) for c in order]
nullv = [cats_null.get(c, 0) for c in order]
x = range(len(order))
ax = axes[0]
ax.bar(x, present, color="#e08a3c", label="live Pages site")
ax.bar(x, nullv, bottom=present, color="#7aa6c2", label="source only")
for i, t in enumerate([p + n for p, n in zip(present, nullv)]):
    ax.text(i, t + 0.5, str(t), ha="center", fontsize=8)
ax.set_xticks(list(x)); ax.set_xticklabels(labels, fontsize=7, rotation=30, ha="left")
ax.set_ylabel("projects")
ax.set_title("Catalog by category: live vs source-only (n=108)", fontsize=9)
ax.legend(fontsize=7); ax.set_ylim(0, 24)
# Right: top source-only reasons
ax2 = axes[1]
reasons = o["source_only_reasons_top"][:7]
rl = [r for r, _ in reasons][::-1]
rv = [v for _, v in reasons][::-1]
ax2.barh(rl, rv, color="#7aa6c2")
for i, v in enumerate(rv):
    ax2.text(v + 0.2, i, str(v), va="center", fontsize=8)
ax2.set_title("Top sourceOnlyReason values (of 62, 26 distinct)", fontsize=9)
ax2.tick_params(axis="y", labelsize=7)
ax2.set_xlim(0, 13)
fig.tight_layout()
out = os.path.join(base, "figures-021", "fig1-catalog.png")
fig.savefig(out)
print("saved", out, os.path.getsize(out))

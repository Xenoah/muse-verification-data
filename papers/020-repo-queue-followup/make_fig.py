import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
base = os.path.expanduser("~/workspace/goals/goal/hidden_files/audit-020")
o = json.load(open(os.path.join(base, "audit-020-results.json")))
fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), dpi=200)
ax = axes[0]
cats = ["Paper 010\n(2026-11-15)", "Paper 020\n(2026-11-20)"]
done = [o["vs_010"]["old_done"], o["status_counter"]["done"]]
pend = [o["vs_010"]["old_pending"], o["status_counter"]["pending"]]
x = range(2)
ax.bar(x, pend, color="#7aa6c2", label="pending")
ax.bar(x, done, bottom=pend, color="#e08a3c", label="done")
for i, t in enumerate([o["vs_010"]["old_total"], o["total_parsed"]]):
    ax.text(i, t + 2, str(t), ha="center", fontsize=9)
ax.set_xticks(list(x)); ax.set_xticklabels(cats, fontsize=8)
ax.set_ylabel("repositories")
ax.set_title("Queue size and status", fontsize=10)
ax.legend(fontsize=8); ax.set_ylim(0, 115)
ax2 = axes[1]
labels = ["New public\n(created >= 11-15)", "Existing private\n(created < 11-15)"]
vals = [o["vs_010"]["added_count"] - o["vs_010"]["added_private"], o["vs_010"]["added_private"]]
ax2.bar(labels, vals, color=["#e08a3c", "#7aa6c2"])
for i, v in enumerate(vals):
    ax2.text(i, v + 0.3, str(v), ha="center", fontsize=9)
ax2.set_ylabel("added in 5 days")
ax2.set_title("Decomposition of +16 inflow", fontsize=10)
ax2.tick_params(axis="x", labelsize=8)
fig.tight_layout()
os.makedirs(os.path.join(base, "figures-020"), exist_ok=True)
out = os.path.join(base, "figures-020", "fig1-queue-followup.png")
fig.savefig(out)
print("saved", out, os.path.getsize(out))

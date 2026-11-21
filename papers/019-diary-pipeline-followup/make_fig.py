import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
base = os.path.expanduser("~/workspace/goals/goal/hidden_files/audit-019")
o = json.load(open(os.path.join(base, "audit-019-results.json")))
days = o["days"]
dates = [d["date"][5:] for d in days]
totals = [d["blog_total_bytes"] for d in days]
fig, ax = plt.subplots(figsize=(9, 3.6), dpi=200)
colors = ["#7aa6c2" if d["date"] < "2026-11-14" else "#e08a3c" for d in days]
ax.bar(dates, totals, color=colors)
ax.axhline(80000, color="#c0392b", linestyle="--", linewidth=1, label="target 80,000")
ax.axhline(100000, color="#7b241c", linestyle=":", linewidth=1, label="cap 100,000")
ax.set_ylabel("bytes (image + index.html, measured)")
ax.set_title("Fig.1 Daily served totals, 2026-11-06..2026-11-19 (blue: paper-007 period, orange: new 6 days)")
ax.legend(fontsize=8)
ax.tick_params(axis="x", labelsize=8, rotation=45)
fig.tight_layout()
out = os.path.join(base, "figures-019", "fig1-daily-totals.png")
fig.savefig(out)
print("saved", out, os.path.getsize(out))

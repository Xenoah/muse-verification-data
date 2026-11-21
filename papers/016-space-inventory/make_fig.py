import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
d=json.load(open("~/workspace/goals/goal/hidden_files/audit-016/audit-016-results.json"))
per=[p for p in d["per_space"] if p["in_catalog"]]
per.sort(key=lambda p:-p["ts_bytes"])
labels=[p["slug"][:18] for p in per]
nm=[p["node_modules_bytes"]/1e6 for p in per]
rest=[(p["ts_bytes"]-p["node_modules_bytes"])/1e6 for p in per]
fig,ax=plt.subplots(figsize=(10,5.2))
y=range(len(per))
ax.barh(y,nm,label="node_modules",color="#4C78A8")
ax.barh(y,rest,left=nm,label="other",color="#F58518")
ax.set_yticks(list(y)); ax.set_yticklabels(labels,fontsize=8)
ax.invert_yaxis()
ax.set_xlabel("MB")
ax.set_title("Paper 016 Fig.1: Per-Space build-tree bytes (node_modules vs other)")
ax.legend()
plt.tight_layout()
plt.savefig("~/workspace/goals/goal/hidden_files/audit-016/figures-016/fig1-spaces.png",dpi=150)
print("fig done")

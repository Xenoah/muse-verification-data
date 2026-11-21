import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json, pathlib
d=json.loads(pathlib.Path.home().joinpath("workspace/goals/goal/hidden_files/audit-018/audit-018-results.json").read_text())
fig,axes=plt.subplots(1,2,figsize=(10,4))
nums=[r["number"] for r in d["explainers"]]
draft=[r["draft"]["chars"] for r in d["explainers"]]
final=[(r["final"]["chars"] if r["final"] else 0) for r in d["explainers"]]
x=range(len(nums)); w=0.38
axes[0].bar([i-w/2 for i in x],draft,w,label="draft")
axes[0].bar([i+w/2 for i in x],final,w,label="final (0 = missing)")
axes[0].set_xticks(list(x)); axes[0].set_xticklabels([f"#{n}" for n in nums])
axes[0].set_ylabel("characters"); axes[0].set_title("Manuscript chars: draft vs final"); axes[0].legend()
labels=["drafts\n5/5","finals\n3/5","measurement\ndays 3/3*","reviews\n(local) 1/5","covers\n(local) 1/5"]
vals=[100,60,100,20,20]
axes[1].bar(labels,vals); axes[1].set_ylabel("% retained"); axes[1].set_title("Retention rate by record type")
axes[1].set_ylim(0,110)
for i,v in enumerate(vals): axes[1].text(i,v+3,f"{v}%",ha="center")
fig.tight_layout()
fig.savefig(pathlib.Path.home()/"workspace/goals/goal/hidden_files/audit-018/figures-018/fig1-retention.png",dpi=150)
print("ok")

import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
res=json.loads((pathlib.Path.home()/"workspace/goals/goal/hidden_files/audit-010/audit-010-results.json").read_text())
langs=res["languages"]
labels=[l for l,_ in langs]; vals=[v for _,v in langs]
fig,axes=plt.subplots(1,2,figsize=(10,4))
axes[0].barh(labels[::-1], vals[::-1], color="#4a7ebb")
axes[0].set_title("Primary language (n=86)")
axes[0].set_xlabel("repos")
axes[1].bar(["done","pending"], [res["counts_from_space"]["done"], res["counts_from_space"]["pending"]], color=["#5a9e6f","#c0c0c0"])
axes[1].set_title("Article status")
axes[1].set_ylabel("repos")
plt.tight_layout()
out=pathlib.Path.home()/"workspace/goals/goal/files/figures-010/fig1-queue.png"
plt.savefig(out, dpi=150)
print(out, out.stat().st_size)

import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
res=json.loads(pathlib.Path("audit-022-results.json").read_text())
fig, axes = plt.subplots(1,2, figsize=(10,4))
sec=res["by_section"]
labels=["papers","explainers","(root)"]
axes[0].bar(["papers","explainers","README"], [sec[s]["files"] for s in labels], color=["#2563eb","#0d9488","#94a3b8"])
axes[0].set_title("Files by section (total 200)")
axes[0].set_ylabel("files")
for i,s in enumerate(labels): axes[0].text(i, sec[s]["files"]+4, str(sec[s]["files"]), ha="center")
axes[1].barh(["script (.py)","results JSON","notes/README (md)","all three"], [16,19,17,16], color="#2563eb")
axes[1].set_title("Paper folders containing each element (of 20)")
axes[1].set_xlim(0,22)
for i,v in enumerate([16,19,17,16]): axes[1].text(v+0.4, i, str(v), va="center")
plt.tight_layout()
out=pathlib.Path("figures-022/fig1-verification-data.png"); out.parent.mkdir(exist_ok=True)
plt.savefig(out, dpi=150); print(out, out.stat().st_size)

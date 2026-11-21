#!/usr/bin/env python3
"""Figure for paper 017, from audit-017-results.json only."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Japanese font if available
for cand in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
             "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
             "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"]:
    if os.path.exists(cand):
        font_manager.fontManager.addfont(cand)
        plt.rcParams["font.family"] = "Noto Sans CJK JP"
        break

d = json.load(open(os.path.expanduser("~/workspace/goals/goal/hidden_files/audit-017/audit-017-results.json")))
tr = d["tracks"]
intents = ["groove", "narrative", "drive", "build", "float", "stillness"]
labels = {"groove": "律動 groove", "narrative": "物語 narrative", "drive": "推進 drive",
          "build": "構築 build", "float": "浮遊 float", "stillness": "静止 stillness"}

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
ax = axes[0]
data = [[t["mp3"]["duration"] for t in tr if t["intent"] == i] for i in intents]
ax.boxplot(data, labels=[f"{labels[i]}\n({len(v)}曲)" for i, v in zip(intents, data)], showfliers=True)
ax.axhline(120, color="red", linestyle="--", linewidth=1)
ax.text(6.45, 121, "2分=120秒", color="red", fontsize=8, ha="right")
ax.set_ylabel("MP3の尺（秒）")
ax.set_title("意図別の尺の分布（全50曲）")
ax.tick_params(axis="x", labelsize=8)

ax = axes[1]
ff = [(t["midi"]["four_floor_bars"] / t["midi"]["bars_with_drum"], t["queue_id"])
      for t in tr if t["midi"]["bars_with_drum"]]
ff.sort(reverse=True)
vals = [v * 100 for v, _ in ff]
ax.bar(range(len(vals)), vals, color="#4a7fb5")
ax.axhline(40, color="red", linestyle="--", linewidth=1)
ax.text(len(vals) - 0.5, 41, "設計上限40%", color="red", fontsize=8, ha="right")
ax.set_xlabel("ドラムのある曲（37曲、四つ打ち比率の降順）")
ax.set_ylabel("四つ打ち小節の比率（%）")
ax.set_title("曲ごとの四つ打ち比率（全体では126/2,249小節=5.6%）")

plt.tight_layout()
out = os.path.expanduser("~/workspace/goals/goal/hidden_files/audit-017/figures-017/fig1-musio-v3.png")
plt.savefig(out, dpi=150)
print("saved", out, os.path.getsize(out))

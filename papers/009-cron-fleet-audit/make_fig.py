#!/usr/bin/env python3
import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

BASE = pathlib.Path(__file__).parent
res = json.loads((BASE/"audit-009-results.json").read_text())
for f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
          "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"]:
    if pathlib.Path(f).exists():
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = "Noto Sans CJK JP"
        break

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
# Panel A: ownership partition (non-overlapping: system 26, goal-owned 17, heartbeat 1)
axes[0].bar(["システム\n管理", "ゴール\n所有", "ハート\nビート"],
            [res["system_jobs"], res["goal_owned"], res["heartbeat_jobs"]],
            color=["#888", "#4a7", "#47a"])
axes[0].set_title("図1a ジョブの所有区分（全44件）")
axes[0].set_ylabel("件数")
# Panel B: top jobs in latest-100 runs window
top = res["runs_by_job_top"][:5]
axes[1].barh([t[0] for t in top][::-1], [t[1] for t in top][::-1], color="#a74")
axes[1].set_title("図1b 直近100実行を占める上位ジョブ")
axes[1].set_xlabel("実行件数（100件中）")
plt.tight_layout()
out = pathlib.Path("~/workspace/goals/goal/files/figures-009/fig1-fleet.png").expanduser()
plt.savefig(out, dpi=150)
print(out, out.stat().st_size)

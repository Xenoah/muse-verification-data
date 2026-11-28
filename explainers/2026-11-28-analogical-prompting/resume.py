import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec=importlib.util.spec_from_file_location("measure", os.path.join(os.path.dirname(os.path.abspath(__file__)),"measure.py"))
# measure.py runs main only under __main__, safe to import
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
OUT=os.path.dirname(os.path.abspath(__file__))
results=json.load(open(os.path.join(OUT,"results_incremental.json")))
# restore RAW from raw_outputs.json to keep appending consistently (separate file for resume)
try:
    m.RAW=json.load(open(os.path.join(OUT,"raw_outputs.json")))
except Exception:
    m.RAW=[]
part=sys.argv[1]
TASKS=m.TASKS
def save():
    json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    json.dump(m.RAW,open(os.path.join(OUT,"raw_outputs.json"),"w"),ensure_ascii=False,indent=1)
if part=="stab":
    # stability currently: T2 x2 reps complete (4), T9 rep0 A only (1). Complete T9 rep0 B and rep1 A/B
    task=[t for t in TASKS if t[0]=="T9"][0]
    r=m.one(task,"B",0.0,42,"T9-stab0-B"); results["stability"].append(r); print("T9 stab0 B",r["correct"],flush=True); save()
    for cond in ("A","B"):
        r=m.one(task,cond,0.0,42,f"T9-stab1-{cond}"); results["stability"].append(r); print("T9 stab1",cond,r["correct"],flush=True); save()
elif part.startswith("sens"):
    idx=int(part[4:])  # 0 or 1: half of seeds
    seeds=[100,101,102,103,104][idx*3:(idx+1)*3] if idx==0 else [100,101,102,103,104][3:]
    # simpler: sens0 -> tasks T2 all seeds, sens1 -> T9 all seeds
    tid="T2" if idx==0 else "T9"
    task=[t for t in TASKS if t[0]==tid][0]
    for s in range(5):
        for cond in ("A","B"):
            r=m.one(task,cond,0.7,100+s,f"{tid}-sens{s}-{cond}")
            results["sensitivity"].append(r); print(tid,"sens",s,cond,r["correct"],flush=True)
        save()
elif part=="final":
    json.dump(results,open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
    for c in ("A","B"):
        n=sum(1 for r in results["main"] if r["cond"]==c and r["correct"])
        print(f"SUMMARY main {c} {n}/12")
    print("stability",len(results["stability"]),"sensitivity",len(results["sensitivity"]))

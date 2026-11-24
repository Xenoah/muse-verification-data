import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure as M
OUT=M.OUT
# load existing raw outputs so we append, not overwrite
M.RAW=json.load(open(os.path.join(OUT,"raw_outputs.json")))
results=json.load(open(os.path.join(OUT,"results_incremental.json")))
tid="T5"
words=[w for i,w in M.TASKS if i==tid][0]; correct=M.ans_of(words)
sens=results["sensitivity"][tid]
al=sens["A"]; bl=sens["B"]
# A has seeds 100,101,102 done; B has 100,101 done. Run B seed102, then both 103,104.
todo=[]
if len(bl)<3: todo.append(("B",102))
for s in (103,104):
    todo.append(("A",s)); todo.append(("B",s))
for cond_name,s in todo:
    fn=M.cot_prompt if cond_name=="A" else M.ltm_prompt
    r=M.cond(fn,words,temp=0.7,seed=s,tag=f"{tid}-{cond_name}-sens{s-100}")
    entry={"seed":s,"answer":r["answer"],"correct":r["answer"]==correct,"gen":r["gen"]}
    (al if cond_name=="A" else bl).append(entry)
    print(tid,"sens",s-100,cond_name,r["answer"],flush=True)
    results["sensitivity"][tid]={"A":al,"B":bl}
    json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
json.dump(results,open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
na=sum(1 for k in results["main"] if results["main"][k]["A"]["correct_flag"]); nb=sum(1 for k in results["main"] if results["main"][k]["B"]["correct_flag"])
print(f"SUMMARY A {na}/8 B {nb}/8",flush=True)

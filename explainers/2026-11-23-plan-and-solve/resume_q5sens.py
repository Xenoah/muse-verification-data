import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure as M
OUT=M.OUT
# restore RAW from previous run so raw_outputs.json stays complete
prev=json.load(open(os.path.join(OUT,"raw_outputs.json")))
M.RAW.extend(prev)
results=json.load(open(os.path.join(OUT,"results_incremental.json")))
qid="Q5"
qtext=[q[1] for q in M.QUESTIONS if q[0]==qid][0]; correct=[q[2] for q in M.QUESTIONS if q[0]==qid][0]
alist=[]; blist=[]
for s in range(5):
    a=M.cond(M.cot_prompt,qtext,temp=0.7,seed=100+s,tag=f"{qid}-A-sens{s}")
    alist.append({"seed":100+s,"answer":a["answer"],"correct":M.close(a["answer"],correct),"gen":a["gen"]})
    b=M.cond(M.psplus_prompt,qtext,temp=0.7,seed=100+s,tag=f"{qid}-B-sens{s}")
    blist.append({"seed":100+s,"answer":b["answer"],"correct":M.close(b["answer"],correct),"gen":b["gen"]})
    print(qid,"sens",s,"A",a["answer"],"B",b["answer"],flush=True)
    results["sensitivity"][qid]={"A":alist,"B":blist}
    json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
json.dump(results,open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
na=sum(1 for k in results["main"] if results["main"][k]["A"]["correct_flag"])
nb=sum(1 for k in results["main"] if results["main"][k]["B"]["correct_flag"])
print(f"SUMMARY A {na}/8 B {nb}/8",flush=True)

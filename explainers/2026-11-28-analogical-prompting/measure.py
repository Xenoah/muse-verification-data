import subprocess, re, json, time, os
BIN="~/workspace/research-002/llama.cpp/build/bin/llama-cli"
MODEL="~/workspace/research-002/models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
OUT=os.path.dirname(os.path.abspath(__file__))
RAW=[]
def extract(raw, full):
    cut=raw.find("\n[ Prompt:")
    if cut<0: cut=raw.find("[ Prompt:")
    body=raw[:cut] if cut>=0 else raw
    starts=[0]
    i=body.rfind(full)
    if i>=0: starts.append(i+len(full))
    j=body.rfind("... (truncated)")
    if j>=0: starts.append(j+len("... (truncated)"))
    k=body.rfind("<|im_start|>assistant\n")
    if k>=0: starts.append(k+len("<|im_start|>assistant\n"))
    return body[max(starts):].strip()
def run(user_prompt, n_tokens, temp=0.0, seed=42, tag=""):
    full=f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
    t0=time.time()
    r=subprocess.run([BIN,"-m",MODEL,"-p",full,"-n",str(n_tokens),"--temp",str(temp),"--seed",str(seed),"-t","4","--no-display-prompt"],capture_output=True,text=True,errors="replace",timeout=900,stdin=subprocess.DEVNULL)
    gen=extract(r.stdout, full)
    dt=round(time.time()-t0,1)
    RAW.append({"tag":tag,"prompt":user_prompt,"temp":temp,"seed":seed,"gen":gen,"time_s":dt})
    json.dump(RAW,open(os.path.join(OUT,"raw_outputs.json"),"w"),ensure_ascii=False,indent=1)
    return gen, dt
TASKS=[
 ("T1","A shop packs 8 apples in each box. Tom buys 3 boxes and also 5 loose apples. How many apples does Tom have in total?",29),
 ("T2","A notebook costs 120 yen. Saki buys 6 notebooks and pays with a 1000 yen bill. How much change does Saki get in yen?",280),
 ("T3","A train travels at 60 kilometers per hour for 2.5 hours. How many kilometers does it travel?",150),
 ("T4","Each bottle holds 500 milliliters. There are 24 bottles. How many liters of water is that in total?",12),
 ("T5","A class has 40 students. Three fifths of the students are boys. How many girls are in the class?",16),
 ("T6","A rectangle is 6 cm wide and 9 cm long. What is half of its area in square centimeters?",27),
 ("T7","A jacket costs 2000 yen. It is sold at 15 percent off. How much does it cost in yen after the discount?",1700),
 ("T8","There are 126 eggs. They are packed into boxes that hold 6 eggs each, with no eggs left over. How many boxes are needed?",21),
 ("T9","Two consecutive whole numbers add up to 25. What is the smaller number?",12),
 ("T10","A test is out of 80 points. A student scores 60 points. What percentage of the full score is that?",75),
 ("T11","Four test scores are 70, 80, 90, and 60. What is their average?",75),
 ("T12","A person walks at 4 kilometers per hour for 45 minutes. How many kilometers does the person walk?",3),
]
def prompt_a(q):
    return f"Question: {q}\nLet's think step by step. Give your final answer on the last line in the form 'Answer: <number>'."
def prompt_b(q):
    return (f"# Problem: {q}\n"
    "# Relevant problems: Recall three relevant and distinct problems. For each problem, describe it briefly and explain its solution step by step with its final answer.\n"
    "# Solve the initial problem: Now solve the initial problem above, following the ideas from the relevant problems. Give your final answer for the initial problem on the last line in the form 'Answer: <number>'.")
def score_gen(gen, gold):
    ms=list(re.finditer(r"Answer:\s*\$?(-?[\d,]+(?:\.\d+)?)", gen))
    fmt=len(ms)>0
    val=None
    if fmt:
        val=float(ms[-1].group(1).replace(",",""))
    else:
        nums=re.findall(r"-?[\d,]+(?:\.\d+)?", gen.replace(",",""))
        if nums: val=float(nums[-1])
    correct=(val is not None and abs(val-gold)<1e-9)
    return {"extracted":val,"format_ok":fmt,"correct":correct}
def one(task, cond, temp, seed, tag):
    tid,q,gold=task
    p = prompt_a(q) if cond=="A" else prompt_b(q)
    n = 320 if cond=="A" else 900
    gen,dt=run(p,n,temp=temp,seed=seed,tag=tag)
    s=score_gen(gen,gold)
    return {"task":tid,"cond":cond,"temp":temp,"seed":seed,"gold":gold,"gen":gen,"time_s":dt,**s}
def main():
    results={"tasks":[{"id":t[0],"question":t[1],"gold":t[2]} for t in TASKS],"main":[],"stability":[],"sensitivity":[]}
    for task in TASKS:
        for cond in ("A","B"):
            r=one(task,cond,0.0,42,f"{task[0]}-main-{cond}")
            results["main"].append(r)
            print(task[0],cond,"correct" if r["correct"] else "WRONG","extracted",r["extracted"],"fmt",r["format_ok"],"gold",r["gold"],flush=True)
        json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    for tid in ("T2","T9"):
        task=[t for t in TASKS if t[0]==tid][0]
        for rep in range(2):
            for cond in ("A","B"):
                r=one(task,cond,0.0,42,f"{tid}-stab{rep}-{cond}")
                results["stability"].append(r)
                print(tid,"stab",rep,cond,"correct" if r["correct"] else "WRONG",flush=True)
            json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    for tid in ("T2","T9"):
        task=[t for t in TASKS if t[0]==tid][0]
        for s in range(5):
            for cond in ("A","B"):
                r=one(task,cond,0.7,100+s,f"{tid}-sens{s}-{cond}")
                results["sensitivity"].append(r)
                print(tid,"sens",s,cond,"correct" if r["correct"] else "WRONG",flush=True)
            json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    json.dump(results,open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
    for c in ("A","B"):
        n=sum(1 for r in results["main"] if r["cond"]==c and r["correct"])
        print(f"SUMMARY main {c} {n}/12",flush=True)
if __name__=="__main__": main()

import subprocess, re, json, time, os
BIN="~/workspace/research-002/llama.cpp/build/bin/llama-cli"
MODEL="~/workspace/research-002/models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
OUT=os.path.dirname(os.path.abspath(__file__))
problems=[
 ("P1","A baker makes 6 trays of 24 cookies. He sells 97 cookies in the morning. How many cookies are left?",47),
 ("P2","Tom has 5 boxes with 18 pencils each. He buys 3 more boxes with 18 pencils each, then gives away 29 pencils. How many pencils does he have now?",115),
 ("P3","A train travels at 65 kilometers per hour for 4 hours, then at 40 kilometers per hour for 3 hours. How many kilometers does it travel in total?",380),
 ("P4","Sara had 240 dollars. She spent 35 dollars on a book and bought 3 shirts at 28 dollars each. How much money does she have left?",121),
 ("P5","There are 7 classes with 26 students each. If 49 students go home early, how many students remain?",133),
 ("P6","A farmer collects 9 baskets of 15 eggs each. Then 23 eggs break. How many eggs are left unbroken?",112),
 ("P7","Ken reads 12 pages per day for 9 days, then 15 pages per day for 4 days. How many pages does he read in total?",168),
 ("P8","A shop had 500 bottles. It sold 137 bottles on Monday and twice as many bottles on Tuesday as on Monday. How many bottles are left?",89),
 ("P9","Maria buys 4 notebooks at 6 dollars each and 2 pens at 3 dollars each. She pays with a 50 dollar bill. How much change does she get?",20),
 ("P10","A parking lot has 8 rows of 22 spaces each. If 156 cars are parked, how many spaces are free?",20),
]
CONDS={
 "A_stepbystep":"Let's think step by step.",
 "B_deepbreath":"Take a deep breath and work on this problem step-by-step.",
 "C_combo":"Let's work together to solve this problem step by step.",
}
def run(prompt, seed=42, temp="0"):
    full=f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    t0=time.time()
    r=subprocess.run([BIN,"-m",MODEL,"-p",full,"-n","256","--temp",temp,"--seed",str(seed),"-t","4","--no-display-prompt"],capture_output=True,text=True,timeout=900,stdin=subprocess.DEVNULL)
    return r.stdout.strip(), round(time.time()-t0,1)
def parse(out):
    m=re.search(r"[Tt]he answer is[:\s]*\$?(-?\d+(?:\.\d+)?)", out)
    if m: return float(m.group(1))
    nums=re.findall(r"-?\d+(?:\.\d+)?", out.replace(",",""))
    return float(nums[-1]) if nums else None
def prompt_for(q, instr):
    return f"{q}\n\n{instr} Then finish with a line in the form: The answer is <number>"
results={c:[] for c in CONDS}
for cname, instr in CONDS.items():
    for pid,q,ans in problems:
        out,t=run(prompt_for(q,instr))
        pred=parse(out)
        results[cname].append({"id":pid,"question":q,"gold":ans,"pred":pred,"correct":pred==ans,"time_s":t,"output":out})
        print(cname,pid,pred,pred==ans,flush=True)
# sensitivity: condition B, temp 0.7, seed 43
sens=[]
for pid,q,ans in problems:
    out,t=run(prompt_for(q,CONDS["B_deepbreath"]),seed=43,temp="0.7")
    pred=parse(out)
    sens.append({"id":pid,"gold":ans,"pred":pred,"correct":pred==ans,"time_s":t,"output":out})
    print("SENS-B-t0.7",pid,pred,pred==ans,flush=True)
# stability: P1,P4,P8 condition B, 3 repeats each (temp 0)
stab=[]
for pid,q,ans in [problems[0],problems[3],problems[7]]:
    outs=[]
    for i in range(3):
        o,_=run(prompt_for(q,CONDS["B_deepbreath"]))
        outs.append({"pred":parse(o),"output":o})
    stab.append({"id":pid,"runs":outs,"all_same_output":len(set(x["output"] for x in outs))==1})
    print("STAB",pid,[x["pred"] for x in outs],flush=True)
def acc(rows): return sum(r["correct"] for r in rows)/len(rows)*100
summary={c:acc(v) for c,v in results.items()}
summary["B_sens_temp0.7_seed43"]=acc(sens)
summary["n_per_condition"]=len(problems)
summary["model"]="Qwen2.5-1.5B-Instruct Q4_K_M"
summary["engine"]="llama.cpp 0.9.0-dev build 1 commit 827466b"
summary["temp"]=0.0; summary["seed"]=42; summary["max_tokens"]=256
json.dump({"summary":summary,"results":results,"sensitivity_B_temp07":sens,"stability":stab},open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
print(json.dumps(summary,ensure_ascii=False))

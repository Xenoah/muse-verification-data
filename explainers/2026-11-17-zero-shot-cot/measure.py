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
def run(prompt, seed=42):
    full=f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    t0=time.time()
    r=subprocess.run([BIN,"-m",MODEL,"-p",full,"-n","256","--temp","0","--seed",str(seed),"-t","4","--no-display-prompt"],capture_output=True,text=True,timeout=600)
    return r.stdout.strip(), round(time.time()-t0,1)
def parse_a(out):
    m=re.findall(r"-?\d+(?:\.\d+)?", out.replace(",",""))
    return float(m[0]) if m else None
def parse_b(out):
    m=re.search(r"[Tt]he answer is[:\s]*\$?(-?\d+(?:\.\d+)?)", out)
    if m: return float(m.group(1))
    nums=re.findall(r"-?\d+(?:\.\d+)?", out.replace(",",""))
    return float(nums[-1]) if nums else None
results=[]
for pid,q,ans in problems:
    pa=f"{q}\n\nAnswer with only the final number, no explanation."
    outa,ta=run(pa); pred_a=parse_a(outa)
    pb=f"{q}\n\nLet's think step by step. Then finish with a line in the form: The answer is <number>"
    outb,tb=run(pb); pred_b=parse_b(outb)
    results.append({"id":pid,"question":q,"gold":ans,"A_pred":pred_a,"A_correct":pred_a==ans,"A_time_s":ta,"A_output":outa,
                    "B_pred":pred_b,"B_correct":pred_b==ans,"B_time_s":tb,"B_output":outb})
    print(pid,"A",pred_a,pred_a==ans,"| B",pred_b,pred_b==ans,flush=True)
# stability: repeat P1,P4,P8 condition B 3 times each
stab=[]
for pid,q,ans in [problems[0],problems[3],problems[7]]:
    pb=f"{q}\n\nLet's think step by step. Then finish with a line in the form: The answer is <number>"
    outs=[]
    for i in range(3):
        o,_=run(pb); outs.append({"pred":parse_b(o),"output":o})
    stab.append({"id":pid,"runs":outs,"all_same_output":len(set(x["output"] for x in outs))==1})
    print("STAB",pid,[x["pred"] for x in outs],flush=True)
acc_a=sum(r["A_correct"] for r in results)/len(results)*100
acc_b=sum(r["B_correct"] for r in results)/len(results)*100
summary={"acc_direct_pct":acc_a,"acc_cot_pct":acc_b,"diff_points":acc_b-acc_a,"n":len(results),
         "model":"Qwen2.5-1.5B-Instruct Q4_K_M","engine":"llama.cpp 0.9.0-dev build 1 commit 827466b","temp":0.0,"seed":42,"max_tokens":256}
json.dump({"summary":summary,"results":results,"stability":stab},open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
print(json.dumps(summary,ensure_ascii=False))

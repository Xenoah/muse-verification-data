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

QUESTIONS=[
 ("Q1","A farmer harvests 120 apples in the morning and 80 apples in the afternoon. He discards 20 damaged apples. He packs the remaining apples into boxes of 5 apples each. How many boxes does he fill?",36.0),
 ("Q2","A school buys 15 packs of pencils. Each pack contains 24 pencils. The school gives 8 pencils to each of 35 students. How many pencils are left?",80.0),
 ("Q3","A train travels at 60 kilometers per hour for 2.5 hours, and then at 40 kilometers per hour for 1.5 hours. How many kilometers does it travel in total?",210.0),
 ("Q4","Sara has 500 dollars. She buys a jacket for 120 dollars. Then she buys 3 shirts that cost 45 dollars each. How much money does she have left in dollars?",245.0),
 ("Q5","A water tank contains 900 liters of water. Water drains out at 15 liters per minute for 20 minutes. Then 250 liters of water are added. How many liters of water are in the tank now?",850.0),
 ("Q6","A book has 480 pages. Ken reads 30 pages per day for 6 days. After that, he reads the remaining pages at 25 pages per day. How many more days will he need to finish the book?",12.0),
 ("Q7","A baker who is 40 years old makes 7 trays of muffins. Each tray holds 12 muffins. He sells 58 muffins in the morning. In the afternoon he bakes 1 more tray of muffins. How many muffins does he have now?",38.0),
 ("Q8","Tom earns 2000 dollars per month. He spends 30 percent of his salary on rent. Of the money remaining after rent, he spends 25 percent on food. How many dollars does he have left after rent and food?",1050.0),
]
def cot_prompt(q):
    return f"Answer the following math word problem.\n\nProblem: {q}\n\nLet's think step by step. Give the final line in exactly this format: Answer: <number>"
def psplus_prompt(q):
    return f"Answer the following math word problem.\n\nProblem: {q}\n\nLet's first understand the problem, extract relevant variables and their corresponding numerals, and make a plan. Then, let's carry out the plan, calculate intermediate variables (pay attention to correct numerical calculation and commonsense), solve the problem step by step, and show the answer. Give the final line in exactly this format: Answer: <number>"
def parse(gen):
    m=list(re.finditer(r"Answer:\s*\$?([0-9][0-9,]*\.?[0-9]*)", gen))
    if not m: return None, False
    try: return float(m[-1].group(1).replace(",","")), True
    except: return None, True
def cond(prompt_fn,q,temp=0.0,seed=42,tag=""):
    gen,t=run(prompt_fn(q),384,temp=temp,seed=seed,tag=tag)
    ans,has=parse(gen)
    return {"gen":gen,"answer":ans,"has_answer_line":has,"time_s":t}
def close(a,b): return a is not None and abs(a-b)<1e-6
def main():
    results={"questions":[{"id":i,"question":q,"correct":c} for i,q,c in QUESTIONS],"main":{},"stability":{},"sensitivity":{}}
    for qid,qtext,correct in QUESTIONS:
        a=cond(cot_prompt,qtext,tag=qid+"-A-main"); a["correct_flag"]=close(a["answer"],correct)
        b=cond(psplus_prompt,qtext,tag=qid+"-B-main"); b["correct_flag"]=close(b["answer"],correct)
        results["main"][qid]={"A":a,"B":b}
        print(qid,"A",a["answer"],a["correct_flag"],"| B",b["answer"],b["correct_flag"],flush=True)
        json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    for qid in ("Q2","Q5"):
        qtext=[q[1] for q in QUESTIONS if q[0]==qid][0]; correct=[q[2] for q in QUESTIONS if q[0]==qid][0]
        lst=[]
        for rep in range(2):
            a=cond(cot_prompt,qtext,tag=f"{qid}-A-stab{rep}"); b=cond(psplus_prompt,qtext,tag=f"{qid}-B-stab{rep}")
            lst.append({"rep":rep,"A_answer":a["answer"],"A_correct":close(a["answer"],correct),"B_answer":b["answer"],"B_correct":close(b["answer"],correct)})
            print(qid,"stab",rep,"A",a["answer"],"B",b["answer"],flush=True)
        results["stability"][qid]=lst
        json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    for qid in ("Q2","Q5"):
        qtext=[q[1] for q in QUESTIONS if q[0]==qid][0]; correct=[q[2] for q in QUESTIONS if q[0]==qid][0]
        alist=[]; blist=[]
        for s in range(5):
            a=cond(cot_prompt,qtext,temp=0.7,seed=100+s,tag=f"{qid}-A-sens{s}")
            alist.append({"seed":100+s,"answer":a["answer"],"correct":close(a["answer"],correct),"gen":a["gen"]})
            b=cond(psplus_prompt,qtext,temp=0.7,seed=100+s,tag=f"{qid}-B-sens{s}")
            blist.append({"seed":100+s,"answer":b["answer"],"correct":close(b["answer"],correct),"gen":b["gen"]})
            print(qid,"sens",s,"A",a["answer"],"B",b["answer"],flush=True)
            results["sensitivity"][qid]={"A":alist,"B":blist}
            json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    json.dump(results,open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
    na=sum(1 for k in results["main"] if results["main"][k]["A"]["correct_flag"])
    nb=sum(1 for k in results["main"] if results["main"][k]["B"]["correct_flag"])
    print(f"SUMMARY A {na}/8 B {nb}/8",flush=True)
if __name__=="__main__":
    main()

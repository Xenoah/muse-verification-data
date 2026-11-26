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
 ("T1","A baker makes 8 trays with 12 rolls on each tray. He sells 57 rolls in the morning and 25 rolls in the afternoon. A sign in the shop says the shop opened in 1998. How many rolls are left?",14),
 ("T2","Mina has 5 boxes with 9 pencils in each box. She gives 7 pencils to her brother and then buys 2 more boxes of 9 pencils. Her brother is 11 years old. How many pencils does Mina have now?",56),
 ("T3","A bus has 48 seats and starts its route completely full. At the first stop, 13 passengers get off and 9 get on. At the second stop, 17 passengers get off and 4 get on. The bus route is 22 kilometers long. How many passengers are on the bus now?",31),
 ("T4","Ken is reading a 240-page book. He reads 35 pages on Monday and 45 pages on Tuesday. On Wednesday he reads twice as many pages as on Monday. His sister is reading a different book with 180 pages. How many pages does Ken have left to read?",90),
 ("T5","A shop sells notebooks for 120 yen each. Saki buys 6 notebooks and pays with a 1000 yen bill. The shop also sells pens for 80 yen each, but Saki does not buy any pens. How much change does Saki get in yen?",280),
 ("T6","A library has 7 shelves with 14 books on each shelf. One day, 23 books are borrowed. The next day, 5 new books are added to each shelf. The library has 3 floors. How many books are on the shelves now?",110),
 ("T7","A farmer collects 126 eggs. He packs all of them into boxes that hold 6 eggs each. He sells 9 boxes. A spare empty box costs 30 yen. How many boxes does the farmer keep?",12),
 ("T8","Yuki scored 18 points in her first game, 24 points in her second game, and 30 points in her third game. Her team had set a target of 100 points for the season. In her fourth game, she scores half as many points as in her third game. How many points has Yuki scored in total across the four games?",87),
 ("T9","A rope is 96 meters long. It is cut into 8 equal pieces. A project uses 3 whole pieces. The rope was bought 5 years ago. How many meters of rope are used for the project?",36),
 ("T10","Tom has 4 bags of marbles with 15 marbles in each bag. He loses 9 marbles. Then he splits all the remaining marbles equally into 3 jars. His friend has 20 marbles. How many marbles are in each jar?",17),
 ("T11","A parking lot has 9 rows with 16 spaces in each row. In the morning, 57 cars are parked there. In the afternoon, 28 more cars arrive and 13 cars leave. The parking lot is 40 meters wide. How many empty spaces are there in the afternoon?",72),
 ("T12","Hana bakes 5 batches of cookies with 24 cookies in each batch. She puts all the cookies into bags of 10 cookies each and gives away 3 full bags. Her oven is 10 years old. How many cookies does Hana have left?",90),
]
def prompt_a(q):
    return f"Question: {q}\nLet's think step by step. Give your final answer on the last line in the form 'Answer: <number>'."
def prompt_b(q):
    return f"Question: {q}\nRead the question again: {q}\nLet's think step by step. Give your final answer on the last line in the form 'Answer: <number>'."
def score_gen(gen, gold):
    ms=list(re.finditer(r"Answer:\s*\$?(-?[\d,]+(?:\.\d+)?)", gen))
    fmt = len(ms)>0
    val=None
    if fmt:
        val=float(ms[-1].group(1).replace(",",""))
    else:
        nums=re.findall(r"-?[\d,]+(?:\.\d+)?", gen.replace(",",""))
        if nums: val=float(nums[-1])
    correct = (val is not None and abs(val-gold)<1e-9)
    return {"extracted":val,"format_ok":fmt,"correct":correct}
def one(task, cond, temp, seed, tag):
    tid,q,gold=task
    p = prompt_a(q) if cond=="A" else prompt_b(q)
    gen,dt=run(p,320,temp=temp,seed=seed,tag=tag)
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
    for tid in ("T3","T10"):
        task=[t for t in TASKS if t[0]==tid][0]
        for rep in range(2):
            for cond in ("A","B"):
                r=one(task,cond,0.0,42,f"{tid}-stab{rep}-{cond}")
                results["stability"].append(r)
                print(tid,"stab",rep,cond,"correct" if r["correct"] else "WRONG",flush=True)
            json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    for tid in ("T3","T10"):
        task=[t for t in TASKS if t[0]==tid][0]
        for s in range(5):
            for cond in ("A","B"):
                r=one(task,cond,0.7,100+s,f"{tid}-sens{s}-{cond}")
                results["sensitivity"].append(r)
                print(tid,"sens",s,cond,"correct" if r["correct"] else "WRONG",flush=True)
            json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    json.dump(results,open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
    a=sum(1 for r in results["main"] if r["cond"]=="A" and r["correct"]); b=sum(1 for r in results["main"] if r["cond"]=="B" and r["correct"])
    print(f"SUMMARY main A {a}/12 B {b}/12",flush=True)
if __name__=="__main__": main()

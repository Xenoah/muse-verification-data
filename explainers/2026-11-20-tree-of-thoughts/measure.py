import subprocess, re, json, time, os
from fractions import Fraction
BIN="~/workspace/research-002/llama.cpp/build/bin/llama-cli"
MODEL="~/workspace/research-002/models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
OUT=os.path.dirname(os.path.abspath(__file__))
PUZZLES=[("P1",[1,2,3,4]),("P2",[4,9,10,13]),("P3",[2,3,4,6]),("P4",[1,5,5,5]),("P5",[3,3,8,8]),("P6",[4,4,10,10])]
RAWLOG=[]
def extract_generation(raw, full_prompt):
    cut=raw.find("\n[ Prompt:")
    if cut<0: cut=raw.find("[ Prompt:")
    body=raw[:cut] if cut>=0 else raw
    starts=[0]
    i=body.rfind(full_prompt)
    if i>=0: starts.append(i+len(full_prompt))
    j=body.rfind("... (truncated)")
    if j>=0: starts.append(j+len("... (truncated)"))
    k=body.rfind("<|im_start|>assistant\n")
    if k>=0: starts.append(k+len("<|im_start|>assistant\n"))
    return body[max(starts):].strip()
def run(user_prompt, n_tokens, temp=0.0, seed=42):
    full=f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
    t0=time.time()
    r=subprocess.run([BIN,"-m",MODEL,"-p",full,"-n",str(n_tokens),"--temp",str(temp),"--seed",str(seed),"-t","4","--no-display-prompt"],capture_output=True,text=True,errors="replace",timeout=900,stdin=subprocess.DEVNULL)
    gen=extract_generation(r.stdout, full)
    RAWLOG.append({"prompt":user_prompt,"temp":temp,"seed":seed,"gen":gen,"raw_tail":r.stdout[-500:]})
    json.dump(RAWLOG,open(os.path.join(OUT,"raw_outputs.json"),"w"),ensure_ascii=False,indent=1)
    return gen, round(time.time()-t0,1)

# ---------- exact arithmetic helpers ----------
def fmt(fr):
    if fr.denominator==1: return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"
def reachable24(nums):
    sols=[]
    def rec(state):
        if len(sols)>0: return True
        if len(state)==1: return state[0]==24
        L=len(state)
        for i in range(L):
            for j in range(L):
                if i==j: continue
                a,b=state[i],state[j]
                rest=[state[k] for k in range(L) if k not in (i,j)]
                for v in (a+b,a-b,a*b,(a/b if b!=0 else None)):
                    if v is None: continue
                    if rec(rest+[v]): return True
        return False
    return rec([Fraction(x) for x in nums])

TOKEN_RE=re.compile(r"\d+\.\d+|\d+/\d+|\d+|[()+\-*/=]")
def eval_expr(expr):
    # safe eval of arithmetic expr with Fractions; returns Fraction or None
    toks=TOKEN_RE.findall(expr)
    if "".join(toks).replace(" ","")!=expr.replace(" ",""): return None
    pos=[0]
    def peek(): return toks[pos[0]] if pos[0]<len(toks) else None
    def parse_expr():
        v=parse_term()
        while peek() in ("+","-"):
            op=toks[pos[0]]; pos[0]+=1
            w=parse_term()
            v=v+w if op=="+" else v-w
        return v
    def parse_term():
        v=parse_factor()
        while peek() in ("*","/"):
            op=toks[pos[0]]; pos[0]+=1
            w=parse_factor()
            if op=="*": v=v*w
            else:
                if w==0: raise ZeroDivisionError
                v=v/w
        return v
    def parse_factor():
        t=peek()
        if t=="(":
            pos[0]+=1; v=parse_expr()
            if peek()!=")": raise ValueError
            pos[0]+=1; return v
        if t=="-":
            pos[0]+=1; return -parse_factor()
        pos[0]+=1
        return Fraction(t)
    try:
        v=parse_expr()
        if pos[0]!=len(toks): return None
        return v
    except Exception:
        return None

def find_success_equation(text, inputs):
    # search for 'expr = 24' or a bare expr line; check uses each input exactly once and ==24
    cands=[]
    for m in re.finditer(r"([0-9][0-9\s()+\-*/\.]*?)\s*=\s*24(?![0-9])", text):
        cands.append(m.group(1))
    for line in text.splitlines():
        line=line.strip().strip(".")
        if line and all(c in "0123456789 ()+-*/." for c in line) and any(op in line for op in "+-*/"):
            cands.append(line)
    for c in cands:
        nums=sorted(int(float(x)) if "." not in x else None for x in re.findall(r"\d+(?:\.\d+)?", c) if "/" not in c)
        # numbers used in expr (integer literals only; inputs are ints)
        lits=[x for x in re.findall(r"\d+", c)]
        if sorted(int(x) for x in lits)!=sorted(inputs): continue
        v=eval_expr(c)
        if v is not None and v==24: return c.strip()
    return None

# ---------- Condition A: CoT ----------
COT_EXAMPLE="""Input: 4 9 10 13
Steps:
13 - 9 = 4 (left: 4, 4, 10)
10 - 4 = 6 (left: 4, 6)
4 * 6 = 24 (left: 24)
Answer: (10 - 4) * (13 - 9) = 24"""
def cot_prompt(nums):
    return ("Solve the Game of 24: use each of the given numbers exactly once with + - * / and parentheses to make 24. "
            "Write 3 intermediate steps in the format 'a op b = c (left: ...)', then a final line 'Answer: <expression> = 24'.\n\n"
            +COT_EXAMPLE+"\n\nInput: "+" ".join(str(x) for x in nums)+"\nSteps:")
def cond_a(nums):
    gen,t=run(cot_prompt(nums),192)
    eq=find_success_equation(gen,nums)
    return {"gen":gen,"success":eq is not None,"equation":eq,"time_s":t}
def cond_a5(nums):
    outs=[]
    for s in range(5):
        gen,t=run(cot_prompt(nums),192,temp=0.7,seed=100+s)
        eq=find_success_equation(gen,nums)
        outs.append({"gen":gen,"success":eq is not None,"equation":eq,"time_s":t,"seed":100+s})
    return {"samples":outs,"success":any(o["success"] for o in outs),"n_success":sum(1 for o in outs if o["success"])}

# ---------- Condition B: ToT-lite BFS b=2 ----------
STEP_RE=re.compile(r"(-?\d+(?:\.\d+)?(?:/\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?(?:/\d+)?)\s*=\s*(-?\d+(?:\.\d+)?(?:/\d+)?)")
def propose_prompt(state):
    nums_str=", ".join(fmt(x) for x in state)
    return ("Game of 24, current numbers: "+nums_str+".\n"
            "Propose up to 5 different possible next steps. Each step picks two of the current numbers and combines them with one operation (+ - * /). "
            "Write each step on its own line in exactly this format: a op b = c (left: remaining numbers after the step)\n"
            "Example: 13 - 9 = 4 (left: 4, 4, 10)\n"
            "Write only the step lines, nothing else.")
def eval_prompt(states):
    lines=[]
    for i,st in enumerate(states,1):
        lines.append(f"{i}. numbers: "+", ".join(fmt(x) for x in st))
    return ("For each set of numbers below, judge whether it is possible to reach exactly 24 using each number exactly once with + - * / and parentheses.\n"
            "Answer one line per set in exactly this format: 1: sure / 2: maybe / 3: impossible (use one of sure, maybe, impossible for each).\n"
            "sure = you can see a way to reach 24, impossible = it clearly cannot reach 24, maybe = unsure.\n"+"\n".join(lines))
def parse_steps(text, state):
    out=[]; seen=set()
    for m in STEP_RE.finditer(text):
        try:
            a=Fraction(m.group(1)); op=m.group(2); b=Fraction(m.group(3)); c=Fraction(m.group(4))
        except Exception: continue
        rest=list(state)
        try:
            rest.remove(a); rest.remove(b)
        except ValueError: continue
        v={"+" : a+b, "-": a-b, "*": a*b, "/": (a/b if b!=0 else None)}[op]
        if v is None or v!=c: continue
        new=tuple(sorted(rest+[c]))
        if new in seen: continue
        seen.add(new)
        out.append({"step":f"{fmt(a)} {op} {fmt(b)} = {fmt(c)}","new_state":list(new)})
        if len(out)>=5: break
    raw_parsed=len(STEP_RE.findall(text))
    return out, raw_parsed
def parse_evals(text, n):
    vals={}
    for m in re.finditer(r"(\d+)\s*[:\.\)]\s*(sure|maybe|impossible)", text.lower()):
        vals[int(m.group(1))]=m.group(2)
    res=[]
    for i in range(1,n+1):
        res.append(vals.get(i))
    return res
SCORE={"sure":3,"maybe":2,"impossible":1}
def cond_b(nums):
    log={"proposals":[],"evals":[]}
    states=[tuple(sorted(Fraction(x) for x in nums))]
    history={states[0]:[]}
    total_prop_parsed=0; total_prop_valid=0
    for depth in range(3):
        cand=[]  # (new_state, history)
        for st in states:
            gen,t=run(propose_prompt(list(st)),160)
            steps,rawn=parse_steps(gen, list(st))
            total_prop_parsed+=rawn; total_prop_valid+=len(steps)
            log["proposals"].append({"state":[fmt(x) for x in st],"gen":gen,"parsed":rawn,"valid":len(steps),"time_s":t})
            for s in steps:
                cand.append((tuple(s["new_state"]), history[st]+[s["step"]]))
        if not cand: return {"success":False,"reason":"no valid proposals at depth "+str(depth+1),"log":log,"prop_parsed":total_prop_parsed,"prop_valid":total_prop_valid}
        # dedupe states
        uniq={}; 
        for ns,h in cand: uniq.setdefault(ns,h)
        cand=list(uniq.items())
        # final depth: check for 24
        if depth==2:
            for ns,h in cand:
                if len(ns)==1 and ns[0]==24:
                    return {"success":True,"path":h,"log":log,"prop_parsed":total_prop_parsed,"prop_valid":total_prop_valid}
            return {"success":False,"reason":"no final state equals 24","final_states":[[fmt(x) for x in ns] for ns,_ in cand],"log":log,"prop_parsed":total_prop_parsed,"prop_valid":total_prop_valid}
        gen,t=run(eval_prompt([list(ns) for ns,_ in cand]),128)
        evals=parse_evals(gen, len(cand))
        scored=[]
        for (ns,h),ev in zip(cand,evals):
            oracle=reachable24(list(ns))
            log["evals"].append({"state":[fmt(x) for x in ns],"eval":ev,"oracle_reachable":oracle})
            scored.append((SCORE.get(ev,2), ns, h))
        scored.sort(key=lambda x:-x[0])
        keep=scored[:2]
        states=[ns for _,ns,_ in keep]
        history={ns:h for _,ns,h in keep}
        log.setdefault("kept",[]).append([[fmt(x) for x in ns] for ns in states])
    return {"success":False,"reason":"loop ended","log":log,"prop_parsed":total_prop_parsed,"prop_valid":total_prop_valid}

results=[]
for pid,nums in PUZZLES:
    row={"id":pid,"puzzle":nums}
    row["A"]=cond_a(nums)
    print(pid,"A",row["A"]["success"],flush=True)
    row["B"]=cond_b(nums)
    print(pid,"B",row["B"]["success"],flush=True)
    results.append(row)
    json.dump({"results":results},open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
for pid,nums in PUZZLES:
    if pid in ("P4","P5","P6"):
        r=next(x for x in results if x["id"]==pid)
        r["A5"]=cond_a5(nums)
        print(pid,"A5",r["A5"]["success"],r["A5"]["n_success"],"/5",flush=True)
        json.dump({"results":results},open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
# stability: repeat A for P2,P5 twice more at temp 0
stab=[]
for pid,nums in PUZZLES:
    if pid in ("P2","P5"):
        reps=[]
        for i in range(2):
            a=cond_a(nums)
            reps.append({"success":a["success"],"gen":a["gen"]})
            print("STAB",pid,i,a["success"],flush=True)
        stab.append({"id":pid,"repeats":reps})
# eval accuracy aggregation
ev_all=[e for r in results for e in r["B"]["log"]["evals"]]
def acc(sub): 
    return (sum(1 for e in sub if (e["eval"]=="sure" and e["oracle_reachable"]) or (e["eval"]=="impossible" and not e["oracle_reachable"])), len(sub))
sure=[e for e in ev_all if e["eval"]=="sure"]; imp=[e for e in ev_all if e["eval"]=="impossible"]; may=[e for e in ev_all if e["eval"]=="maybe"]; non=[e for e in ev_all if e["eval"] is None]
summary={
 "A_success":sum(1 for r in results if r["A"]["success"]),"B_success":sum(1 for r in results if r["B"]["success"]),"n":len(results),
 "A5":{r["id"]:{"any":r["A5"]["success"],"n_success":r["A5"]["n_success"]} for r in results if "A5" in r},
 "prop_parsed_total":sum(r["B"]["prop_parsed"] for r in results),"prop_valid_total":sum(r["B"]["prop_valid"] for r in results),
 "evals_total":len(ev_all),"eval_sure":{"n":len(sure),"correct":sum(1 for e in sure if e["oracle_reachable"])},
 "eval_impossible":{"n":len(imp),"correct":sum(1 for e in imp if not e["oracle_reachable"])},
 "eval_maybe":{"n":len(may),"oracle_reachable":sum(1 for e in may if e["oracle_reachable"])},
 "eval_unparsed":len(non),
 "model":"Qwen2.5-1.5B-Instruct Q4_K_M","engine":"llama.cpp 0.9.0-dev build 1 commit 827466b"}
json.dump({"summary":summary,"results":results,"stability":stab},open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
print(json.dumps(summary,ensure_ascii=False))

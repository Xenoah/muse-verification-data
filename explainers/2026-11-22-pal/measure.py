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
 ("Q1","Janet's ducks lay 16 eggs per day. She eats three for breakfast every morning and bakes muffins for her friends every day with four eggs. She sells the remainder at the farmers' market daily for $2 per fresh duck egg. How much in dollars does she make every day at the farmers' market?",18.0),
 ("Q2","A warehouse stores 1247 boxes. Each box contains 36 identical items. How many items are stored in the warehouse in total?",44892.0),
 ("Q3","A factory produces 18473 bottles per day. It operates for 27 days. During that period, 12345 bottles are found to be defective and are discarded. How many non-defective bottles remain?",486426.0),
 ("Q4","Ken has $1000. He buys 48 notebooks that cost $13.75 each. How much money does he have left in dollars?",340.0),
 ("Q5","A prize of $98280 is shared equally among 24 workers. How many dollars does each worker receive?",4095.0),
 ("Q6","A jacket originally costs 12500 yen. Its price is first raised by 8 percent, and the new price is then discounted by 15 percent. What is the final price in yen?",11475.0),
 ("Q7","Mina has 3 chairs, 5 apples, 2 desks, 7 oranges, 4 bananas, 1 lamp, and 6 peaches. How many fruits does Mina have in total?",22.0),
 ("Q8","A printing company prints 234567 pages in one batch. It completes 89 batches. How many pages does it print in total?",20876463.0),
]
FEWSHOT="""Solve each math word problem by writing a Python program. Use meaningful variable names. End the program with a variable named result that holds the final answer. Output only Python code, no explanations.

Problem: Olivia has $23. She bought five bagels for $3 each. How much money does she have left?
Solution:
money_initial = 23
bagels = 5
bagel_cost = 3
money_spent = bagels * bagel_cost
money_left = money_initial - money_spent
result = money_left

Problem: A gardener plants 12 rows of trees. Each row has 14 trees. 9 trees die. How many trees are alive?
Solution:
rows = 12
trees_per_row = 14
total_trees = rows * trees_per_row
dead_trees = 9
result = total_trees - dead_trees

"""
def cot_prompt(q):
    return f"Answer the following math word problem. Think step by step, then give the final line in exactly this format: Answer: <number>\n\nProblem: {q}"
def pal_prompt(q):
    return FEWSHOT+f"Problem: {q}\nSolution:\n"
def parse_cot(gen):
    m=list(re.finditer(r"Answer:\s*\$?([0-9][0-9,]*\.?[0-9]*)", gen))
    if not m: return None, False
    try: return float(m[-1].group(1).replace(",","")), True
    except: return None, True
def exec_pal(gen):
    # extract code lines: keep lines that look like python assignments/expressions
    code=gen
    # cut at next Problem: if model continues
    for stop in ["\nProblem:", "\nProblem :"]:
        i=code.find(stop)
        if i>=0: code=code[:i]
    # remove markdown fences
    code=code.replace("```python","").replace("```","")
    lines=[]
    for ln in code.splitlines():
        s=ln.strip()
        if not s: continue
        if s.startswith("#"): continue
        if re.match(r"^(result|[A-Za-z_][A-Za-z0-9_]*)\s*=", s) or s.startswith(("for ","if ","result =")):
            lines.append(s)
        elif lines and (s[0].isdigit() or s[0] in "+-*/).,"):
            lines[-1]+=s
    code_clean="\n".join(lines)
    if not code_clean or "result" not in code_clean:
        return None, code_clean, "format: no code or no result variable"
    if re.search(r"\b(import|open|print|input|eval|exec|__|while|def)\b", code_clean):
        return None, code_clean, "format: forbidden construct"
    try:
        env={}
        exec(compile(code_clean,"<pal>","exec"), {"__builtins__": {}}, env)
        val=env.get("result")
        if val is None or not isinstance(val,(int,float)):
            return None, code_clean, "format: result not numeric"
        return float(val), code_clean, None
    except Exception as e:
        return None, code_clean, f"exec_error: {type(e).__name__}: {e}"
def cond_a(q,temp=0.0,seed=42,tag="A"):
    gen,t=run(cot_prompt(q),384,temp=temp,seed=seed,tag=tag)
    ans,has=parse_cot(gen)
    return {"gen":gen,"answer":ans,"has_answer_line":has,"time_s":t}
def cond_b(q,temp=0.0,seed=42,tag="B"):
    gen,t=run(pal_prompt(q),256,temp=temp,seed=seed,tag=tag)
    ans,code,err=exec_pal(gen)
    return {"gen":gen,"code":code,"exec_error":err,"answer":ans,"time_s":t}
def close(a,b): return a is not None and abs(a-b)<1e-6
def main():
    results={"questions":[{"id":i,"question":q,"correct":c} for i,q,c in QUESTIONS],"main":{},"stability":{},"sensitivity":{}}
    for qid,qtext,correct in QUESTIONS:
        a=cond_a(qtext,tag=qid+"-A-main"); a["correct_flag"]=close(a["answer"],correct)
        b=cond_b(qtext,tag=qid+"-B-main"); b["correct_flag"]=close(b["answer"],correct)
        b["failure_type"]=None if b["correct_flag"] else ("format" if b["exec_error"] else "content")
        results["main"][qid]={"A":a,"B":b}
        print(qid,"A",a["answer"],a["correct_flag"],"| B",b["answer"],b["correct_flag"],b["exec_error"] or "",flush=True)
        json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    for qid in ("Q2","Q8"):
        qtext=[q[1] for q in QUESTIONS if q[0]==qid][0]; correct=[q[2] for q in QUESTIONS if q[0]==qid][0]
        lst=[]
        for rep in range(2):
            a=cond_a(qtext,tag=f"{qid}-A-stab{rep}"); b=cond_b(qtext,tag=f"{qid}-B-stab{rep}")
            lst.append({"rep":rep,"A_answer":a["answer"],"A_correct":close(a["answer"],correct),"B_answer":b["answer"],"B_correct":close(b["answer"],correct),"B_code":b["code"],"B_error":b["exec_error"]})
            print(qid,"stab",rep,"A",a["answer"],"B",b["answer"],flush=True)
        results["stability"][qid]=lst
        json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    for qid in ("Q2","Q8"):
        qtext=[q[1] for q in QUESTIONS if q[0]==qid][0]; correct=[q[2] for q in QUESTIONS if q[0]==qid][0]
        alist=[]; blist=[]
        for s in range(5):
            a=cond_a(qtext,temp=0.7,seed=100+s,tag=f"{qid}-A-sens{s}")
            alist.append({"seed":100+s,"answer":a["answer"],"correct":close(a["answer"],correct),"gen":a["gen"]})
            b=cond_b(qtext,temp=0.7,seed=100+s,tag=f"{qid}-B-sens{s}")
            blist.append({"seed":100+s,"answer":b["answer"],"correct":close(b["answer"],correct),"code":b["code"],"error":b["exec_error"],"gen":b["gen"]})
            print(qid,"sens",s,"A",a["answer"],"B",b["answer"],flush=True)
            results["sensitivity"][qid]={"A":alist,"B":blist}
            json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    json.dump(results,open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
    na=sum(1 for k in results["main"] if results["main"][k]["A"]["correct_flag"])
    nb=sum(1 for k in results["main"] if results["main"][k]["B"]["correct_flag"])
    print(f"SUMMARY A {na}/8 B {nb}/8",flush=True)
if __name__=="__main__":
    main()

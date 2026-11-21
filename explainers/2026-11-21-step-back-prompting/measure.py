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
 ("Q1","An ideal gas is in a sealed container with a movable piston. The temperature of the gas is increased by a factor of 3, and the volume is increased by a factor of 6. What happens to the pressure of the gas?\nA) It increases by a factor of 3\nB) It decreases to 1/2 of the original\nC) It stays the same\nD) It increases by a factor of 18","B",["ideal gas","pv","nrt","p =","pressure proportional","t/v","temperature divided"]),
 ("Q2","A sample of an unknown chloride compound is dissolved in water and titrated with excess Pb(NO3)2, forming a precipitate of PbCl2. After drying, there are 0.010 mol of PbCl2 precipitate. The molar mass of chlorine is 35.45 g/mol. What is the mass of chloride in the original sample?\nA) 0.355 g\nB) 0.709 g\nC) 1.418 g\nD) 0.177 g","B",["pbcl2","2 mol","two","stoichiometr","0.020","35.45"]),
 ("Q3","A solid block floats in water with 75% of its volume submerged. The density of water is 1000 kg/m3. What is the density of the block?\nA) 250 kg/m3\nB) 1000 kg/m3\nC) 750 kg/m3\nD) 1333 kg/m3","C",["archimedes","buoyan","displaced","fraction","0.75","submerged fraction"]),
 ("Q4","A resistor has a fixed resistance. The voltage across it is increased by a factor of 2. By what factor does the electrical power dissipated in the resistor change?\nA) It increases by a factor of 2\nB) It increases by a factor of 4\nC) It increases by a factor of 8\nD) It stays the same","B",["p = v","v^2","v2/r","power proportional to the square","square of the voltage","ohm"]),
 ("Q5","A ball's speed is increased by a factor of 3, while its mass stays the same. By what factor does its kinetic energy change?\nA) It increases by a factor of 3\nB) It increases by a factor of 6\nC) It increases by a factor of 9\nD) It increases by a factor of 27","C",["kinetic energy","1/2","mv^2","square","v^2","proportional to the square"]),
 ("Q6","The concentration of hydrogen ions [H+] in a solution is increased by a factor of 100. How does the pH of the solution change?\nA) It increases by 2\nB) It decreases by 2\nC) It decreases by 100\nD) It stays the same","B",["ph = -log","logarithm","log","-log10","base 10"]),
 ("Q7","The length of a simple pendulum is increased by a factor of 4. By what factor does its period change?\nA) It increases by a factor of 4\nB) It increases by a factor of 2\nC) It increases by a factor of 16\nD) It stays the same","B",["pendulum","t = 2","sqrt","square root","proportional to the square root"]),
 ("Q8","A price is first increased by 20%, and the new price is then decreased by 20%. Compared with the original price, what is the final price?\nA) Exactly the same as the original\nB) 4% higher than the original\nC) 4% lower than the original\nD) 20% lower than the original","C",["multiply","1.2","0.8","factor","successive","0.96"]),
]
EXEMPLAR_Q="Two charged particles are separated by a distance r. The distance is increased by a factor of 2. What happens to the electric force between them?"
EXEMPLAR_P="Coulomb's law: the electric force is inversely proportional to the square of the distance, F = k * q1 * q2 / r^2. If r doubles, F becomes 1/4 of the original."
def cot_prompt(qtext):
    return f"Answer the following multiple-choice question. Think step by step, then give the final line in exactly this format: Answer: X (where X is A, B, C, or D).\n\nQuestion: {qtext}\n\nLet's think step by step."
def step1_prompt(qtext):
    return ("You are an expert at physics and chemistry. You are given a problem. Your task is to extract the concepts and principles involved in solving the problem. Do NOT solve the problem yet. Only state the relevant principle(s), including any formula and what each quantity means.\n\n"
            f"Question: {EXEMPLAR_Q}\nPrinciples Involved: {EXEMPLAR_P}\n\n"
            f"Question: {qtext}\nPrinciples Involved:")
def step2_prompt(qtext, principles):
    return (f"You are an expert at physics and chemistry. Solve the following problem step by step by following the principles given below. Then give the final line in exactly this format: Answer: X (where X is A, B, C, or D).\n\nQuestion: {qtext}\n\nPrinciples: {principles}\n\nAnswer:")
def parse_answer(gen):
    m=list(re.finditer(r"Answer:\s*\(?([A-D])\b", gen))
    if m: return m[-1].group(1)
    m=list(re.finditer(r"\b([A-D])\)", gen[-200:]))
    return None
def principle_ok(principles, keys):
    low=principles.lower()
    hits=[k for k in keys if k in low]
    return hits
def cond_a(qtext, temp=0.0, seed=42, tag="A"):
    gen,t=run(cot_prompt(qtext),512,temp=temp,seed=seed,tag=tag)
    return {"gen":gen,"answer":parse_answer(gen),"time_s":t}
def cond_b(qtext, temp=0.0, seed=42, tag="B"):
    pgen,pt=run(step1_prompt(qtext),140,temp=temp,seed=seed,tag=tag+"-step1")
    gen,t=run(step2_prompt(qtext,pgen),384,temp=temp,seed=seed,tag=tag+"-step2")
    return {"principles":pgen,"principles_time_s":pt,"gen":gen,"answer":parse_answer(gen),"time_s":t}

def main():
    results={"questions":[],"main":{},"stability":{},"sensitivity":{}}
    for qid,qtext,correct,keys in QUESTIONS:
        results["questions"].append({"id":qid,"question":qtext,"correct":correct,"principle_keys":keys})
        a=cond_a(qtext,tag=qid+"-A-main")
        a["correct_flag"]=(a["answer"]==correct)
        b=cond_b(qtext,tag=qid+"-B-main")
        b["correct_flag"]=(b["answer"]==correct)
        b["principle_hits"]=principle_ok(b["principles"],keys)
        b["principle_ok"]=len(b["principle_hits"])>=1
        results["main"][qid]={"A":a,"B":b}
        print(qid,"A",a["answer"],a["correct_flag"],"| B",b["answer"],b["correct_flag"],"| princ hits",b["principle_hits"],flush=True)
        json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    # stability: Q1, Q4 temp0 x2 extra
    for qid in ("Q1","Q4"):
        qtext=[q[1] for q in QUESTIONS if q[0]==qid][0]
        correct=[q[2] for q in QUESTIONS if q[0]==qid][0]
        lst=[]
        for rep in range(2):
            a=cond_a(qtext,tag=f"{qid}-A-stab{rep}")
            b=cond_b(qtext,tag=f"{qid}-B-stab{rep}")
            lst.append({"rep":rep,"A_answer":a["answer"],"A_correct":a["answer"]==correct,"B_answer":b["answer"],"B_correct":b["answer"]==correct,"B_principles":b["principles"]})
            print(qid,"stab",rep,"A",a["answer"],"B",b["answer"],flush=True)
        results["stability"][qid]=lst
        json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    # sensitivity: Q1, Q8 temp0.7 x5
    for qid in ("Q1","Q8"):
        qtext=[q[1] for q in QUESTIONS if q[0]==qid][0]
        correct=[q[2] for q in QUESTIONS if q[0]==qid][0]
        keys=[q[3] for q in QUESTIONS if q[0]==qid][0]
        alist=[]; blist=[]
        for s in range(5):
            a=cond_a(qtext,temp=0.7,seed=100+s,tag=f"{qid}-A-sens{s}")
            alist.append({"seed":100+s,"answer":a["answer"],"correct":a["answer"]==correct,"gen":a["gen"]})
            b=cond_b(qtext,temp=0.7,seed=100+s,tag=f"{qid}-B-sens{s}")
            blist.append({"seed":100+s,"answer":b["answer"],"correct":b["answer"]==correct,"principles":b["principles"],"principle_hits":principle_ok(b["principles"],keys),"gen":b["gen"]})
            print(qid,"sens",s,"A",a["answer"],"B",b["answer"],flush=True)
            results["sensitivity"][qid]={"A":alist,"B":blist}
            json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    json.dump(results,open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
    # summary
    na=sum(1 for qid in results["main"] if results["main"][qid]["A"]["correct_flag"])
    nb=sum(1 for qid in results["main"] if results["main"][qid]["B"]["correct_flag"])
    npok=sum(1 for qid in results["main"] if results["main"][qid]["B"]["principle_ok"])
    print(f"SUMMARY A {na}/8 B {nb}/8 principle_ok {npok}/8",flush=True)

if __name__=="__main__":
    main()

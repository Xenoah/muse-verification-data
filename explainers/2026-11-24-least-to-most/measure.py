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

# word lists (self-made); answer = concatenation of last letters
TASKS=[
 ("T1",["apple","dog","sun","book","tree","fish"]),
 ("T2",["cat","house","pen","egg","door","milk"]),
 ("T3",["bird","cake","wolf","lamp","star","moon","road","king"]),
 ("T4",["frog","desk","ship","bell","snow","leaf","ring","song"]),
 ("T5",["tiger","cloud","stone","river","plant","horse","bread","chair","glass","mouse"]),
 ("T6",["snake","train","apple","ocean","piano","zebra","lemon","tower","sugar","watch"]),
 ("T7",["rabbit","garden","window","pencil","monkey","dolphin","orange","silver","winter","summer","flower","mother"]),
 ("T8",["dragon","castle","forest","rocket","planet","pirate","wizard","knight","bridge","island","temple","saddle"]),
]
def ans_of(words): return "".join(w[-1] for w in words)

COT_EXEMPLARS="""Q: Take the last letters of each word in "think, machine" and concatenate them.
A: The last letter of "think" is "k". The last letter of "machine" is "e". Concatenating them is "ke". The answer is: ke.

Q: Take the last letters of each word in "think, machine, learning" and concatenate them.
A: The last letter of "think" is "k". The last letter of "machine" is "e". The last letter of "learning" is "g". Concatenating them is "keg". The answer is: keg."""

LTM_EXEMPLARS="""Q: Take the last letters of each word in "think, machine, learning" and concatenate them.
A: Let's break down this problem: 1. Take the last letters of "think, machine" and concatenate them. 2. Take the last letter of "learning" and concatenate it to the answer of subproblem 1.
1. The last letter of "think" is "k". The last letter of "machine" is "e". Concatenating them is "ke".
2. The last letter of "learning" is "g". Concatenating "ke" and "g" is "keg".
The answer is: keg.

Q: Take the last letters of each word in "think, machine, learning, artificial" and concatenate them.
A: Let's break down this problem: 1. Take the last letters of "think, machine" and concatenate them. 2. Take the last letter of "learning" and concatenate it to the answer of subproblem 1. 3. Take the last letter of "artificial" and concatenate it to the answer of subproblem 2.
1. The last letter of "think" is "k". The last letter of "machine" is "e". Concatenating them is "ke".
2. The last letter of "learning" is "g". Concatenating "ke" and "g" is "keg".
3. The last letter of "artificial" is "l". Concatenating "keg" and "l" is "kegl".
The answer is: kegl."""

def cot_prompt(words):
    lst=", ".join(words)
    return f"{COT_EXEMPLARS}\n\nQ: Take the last letters of each word in \"{lst}\" and concatenate them.\nA: Think step by step, then give the final line in exactly this format: Answer: <string>"
def ltm_prompt(words):
    lst=", ".join(words)
    return f"{LTM_EXEMPLARS}\n\nQ: Take the last letters of each word in \"{lst}\" and concatenate them.\nA: First break the problem down into subproblems (start with the first two words, then add one word at a time), solve each subproblem in order using the answer of the previous subproblem, then give the final line in exactly this format: Answer: <string>"

def parse(gen):
    m=list(re.finditer(r"Answer:\s*\**([A-Za-z]+)", gen))
    if not m: return None, False
    return m[-1].group(1).lower(), True
def cond(fn,words,temp=0.0,seed=42,tag=""):
    gen,t=run(fn(words),512,temp=temp,seed=seed,tag=tag)
    a,has=parse(gen)
    return {"gen":gen,"answer":a,"has_answer_line":has,"time_s":t}
def main():
    results={"tasks":[{"id":i,"words":w,"correct":ans_of(w)} for i,w in TASKS],"main":{},"stability":{},"sensitivity":{}}
    for tid,words in TASKS:
        correct=ans_of(words)
        a=cond(cot_prompt,words,tag=tid+"-A-main"); a["correct_flag"]=(a["answer"]==correct)
        b=cond(ltm_prompt,words,tag=tid+"-B-main"); b["correct_flag"]=(b["answer"]==correct)
        results["main"][tid]={"A":a,"B":b}
        print(tid,len(words),correct,"A",a["answer"],a["correct_flag"],"| B",b["answer"],b["correct_flag"],flush=True)
        json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    for tid in ("T3","T5"):
        words=[w for i,w in TASKS if i==tid][0]; correct=ans_of(words); lst=[]
        for rep in range(2):
            a=cond(cot_prompt,words,tag=f"{tid}-A-stab{rep}"); b=cond(ltm_prompt,words,tag=f"{tid}-B-stab{rep}")
            lst.append({"rep":rep,"A_answer":a["answer"],"A_correct":a["answer"]==correct,"B_answer":b["answer"],"B_correct":b["answer"]==correct})
            print(tid,"stab",rep,"A",a["answer"],"B",b["answer"],flush=True)
        results["stability"][tid]=lst; json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    for tid in ("T3","T5"):
        words=[w for i,w in TASKS if i==tid][0]; correct=ans_of(words); al=[]; bl=[]
        for s in range(5):
            a=cond(cot_prompt,words,temp=0.7,seed=100+s,tag=f"{tid}-A-sens{s}"); al.append({"seed":100+s,"answer":a["answer"],"correct":a["answer"]==correct,"gen":a["gen"]})
            b=cond(ltm_prompt,words,temp=0.7,seed=100+s,tag=f"{tid}-B-sens{s}"); bl.append({"seed":100+s,"answer":b["answer"],"correct":b["answer"]==correct,"gen":b["gen"]})
            print(tid,"sens",s,"A",a["answer"],"B",b["answer"],flush=True)
            results["sensitivity"][tid]={"A":al,"B":bl}; json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    json.dump(results,open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
    na=sum(1 for k in results["main"] if results["main"][k]["A"]["correct_flag"]); nb=sum(1 for k in results["main"] if results["main"][k]["B"]["correct_flag"])
    print(f"SUMMARY A {na}/8 B {nb}/8",flush=True)
if __name__=="__main__": main()

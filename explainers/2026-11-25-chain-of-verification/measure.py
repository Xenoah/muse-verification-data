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
 ("T1","Name some chemical elements that are noble gases.","a noble gas (a chemical element in Group 18 of the periodic table)",
  ["helium","neon","argon","krypton","xenon","radon","oganesson"]),
 ("T2","Name some countries that share a land border with France in Europe.","a country that shares a land border with France in Europe",
  ["belgium","luxembourg","germany","switzerland","italy","spain","andorra","monaco"]),
 ("T3","Name some US states whose name starts with the letter M.","a US state whose name starts with the letter M",
  ["maine","maryland","massachusetts","michigan","minnesota","mississippi","missouri","montana"]),
 ("T4","Name some prime numbers that are greater than 30 and less than 60.","a prime number greater than 30 and less than 60",
  ["31","37","41","43","47","53","59"]),
 ("T5","Name some mammals that lay eggs.","a mammal that lays eggs (a monotreme)",
  ["platypus","short-beaked echidna","eastern long-beaked echidna","western long-beaked echidna","sir david's long-beaked echidna","attenborough's long-beaked echidna","long-beaked echidna","echidna"]),
 ("T6","Name some dwarf planets officially recognized by the IAU.","a dwarf planet officially recognized by the IAU (International Astronomical Union)",
  ["pluto","eris","haumea","makemake","ceres"]),
 ("T7","Name some moons of Jupiter that were discovered by Galileo (the Galilean moons).","a moon of Jupiter discovered by Galileo (a Galilean moon)",
  ["io","europa","ganymede","callisto"]),
 ("T8","Name some founding member countries of the European Community that signed the Treaty of Rome in 1957.","a founding member country of the European Community that signed the Treaty of Rome in 1957",
  ["belgium","france","italy","luxembourg","netherlands","germany","west germany"]),
]
def norm(s):
    s=s.strip().lower().strip(".*-•0123456789) ").replace("the ","",1) if not s.strip().isdigit() else s.strip()
    return s.strip(" .")
def parse_list(gen):
    # take first non-empty line(s) up to blank line, split by comma or newline
    txt=gen.strip()
    if not txt: return []
    # cut explanations after a blank line
    first=txt.split("\n\n")[0]
    parts=re.split(r"[,\n;]", first)
    items=[]
    for p in parts:
        p=re.sub(r"^\s*(?:[-*]\s+|\d+[\.\)]\s+)","",p).strip(" .")
        p=re.sub(r"\s*\(.*?\)\s*$","",p).strip()
        if p and len(p)<60: items.append(p)
    # dedupe preserving order (normalized)
    seen=set(); out=[]
    for it in items:
        n=norm(it)
        if n not in seen: seen.add(n); out.append(it)
    return out[:12]
def score(items, gold):
    pos=[]; neg=[]
    for it in items:
        (pos if norm(it) in gold else neg).append(it)
    prec=(len(pos)/len(items)) if items else 0.0
    return {"items":items,"pos":pos,"neg":neg,"n":len(items),"n_pos":len(pos),"n_neg":len(neg),"precision":round(prec,4)}
def verify_one(item, pred, temp, seed, tag):
    q=f"Is \"{item}\" {pred}? Answer with Yes or No first, then a brief reason in one short sentence."
    gen,dt=run(q,80,temp=temp,seed=seed,tag=tag)
    head=gen.strip()[:200].lower()
    m=re.search(r"\b(yes|no)\b", head)
    verdict=m.group(1) if m else "unknown"
    return {"item":item,"question":q,"gen":gen,"verdict":verdict,"time_s":dt}
def pipeline(task, temp=0.0, seed=42, tagprefix=""):
    tid,question,pred,gold=task
    gen,dt=run(f"{question} List only the answers, separated by a comma.",256,temp=temp,seed=seed,tag=tagprefix+"-baseline")
    items=parse_list(gen)
    base=score(items,gold); base["gen"]=gen; base["time_s"]=dt
    vers=[]; kept=[]
    for it in items:
        v=verify_one(it,pred,temp,seed,tagprefix+f"-verify-{norm(it)[:20]}")
        vers.append(v)
        if v["verdict"]=="yes": kept.append(it)
    final=score(kept,gold)
    return {"baseline":base,"verifications":vers,"final":final}
def main():
    results={"tasks":[{"id":t[0],"question":t[1],"gold":t[3]} for t in TASKS],"main":{},"stability":{},"sensitivity":{}}
    for task in TASKS:
        tid=task[0]
        r=pipeline(task,tagprefix=tid+"-main")
        results["main"][tid]=r
        print(tid,"base prec",r["baseline"]["precision"],r["baseline"]["n_pos"],"/",r["baseline"]["n"],"| final prec",r["final"]["precision"],r["final"]["n_pos"],"/",r["final"]["n"],flush=True)
        json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    for tid in ("T2","T4"):
        task=[t for t in TASKS if t[0]==tid][0]; lst=[]
        for rep in range(2):
            r=pipeline(task,tagprefix=f"{tid}-stab{rep}")
            lst.append({"rep":rep,"base_precision":r["baseline"]["precision"],"base_pos":r["baseline"]["n_pos"],"base_n":r["baseline"]["n"],"final_precision":r["final"]["precision"],"final_pos":r["final"]["n_pos"],"final_n":r["final"]["n"]})
            print(tid,"stab",rep,lst[-1],flush=True)
        results["stability"][tid]=lst; json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    for tid in ("T2","T4"):
        task=[t for t in TASKS if t[0]==tid][0]; lst=[]
        for s in range(5):
            r=pipeline(task,temp=0.7,seed=100+s,tagprefix=f"{tid}-sens{s}")
            lst.append({"seed":100+s,"base_precision":r["baseline"]["precision"],"base_pos":r["baseline"]["n_pos"],"base_n":r["baseline"]["n"],"final_precision":r["final"]["precision"],"final_pos":r["final"]["n_pos"],"final_n":r["final"]["n"],"base_items":r["baseline"]["items"],"final_items":r["final"]["items"]})
            print(tid,"sens",s,lst[-1]["base_precision"],"->",lst[-1]["final_precision"],flush=True)
            results["sensitivity"][tid]=lst; json.dump(results,open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
    json.dump(results,open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
    bp=sum(results["main"][t]["baseline"]["n_pos"] for t in results["main"]); bn=sum(results["main"][t]["baseline"]["n"] for t in results["main"])
    fp=sum(results["main"][t]["final"]["n_pos"] for t in results["main"]); fn=sum(results["main"][t]["final"]["n"] for t in results["main"])
    print(f"SUMMARY pooled baseline precision {bp}/{bn}={bp/bn if bn else 0:.3f} final {fp}/{fn}={fp/fn if fn else 0:.3f}",flush=True)
if __name__=="__main__": main()

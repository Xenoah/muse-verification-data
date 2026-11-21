import subprocess, re, json, time, os
BIN="~/workspace/research-002/llama.cpp/build/bin/llama-cli"
MODEL="~/workspace/research-002/models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
OUT=os.path.dirname(os.path.abspath(__file__))
TASKS=[
 ("T1",["cat","garden","moon","bicycle","whisper"]),
 ("T2",["robot","library","coffee","rain","key"]),
 ("T3",["mountain","chef","violin","snow","map"]),
 ("T4",["teacher","ocean","clock","apple","bridge"]),
 ("T5",["dog","market","sun","book","hat"]),
 ("T6",["dragon","castle","river","song","stone"]),
]
RAWLOG=[]
def extract_generation(raw, full_prompt):
    # llama-cli output = banner + "> " + prompt echo (possibly truncated with
    # "... (truncated)") + generation + stats line. Generation starts after
    # the LATEST of: full prompt text, truncated marker, assistant marker.
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
    gen=body[max(starts):]
    return gen.strip()
def run(user_prompt, n_tokens, seed=42):
    full=f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
    t0=time.time()
    r=subprocess.run([BIN,"-m",MODEL,"-p",full,"-n",str(n_tokens),"--temp","0","--seed",str(seed),"-t","4","--no-display-prompt"],capture_output=True,text=True,errors="replace",timeout=900,stdin=subprocess.DEVNULL)
    RAWLOG.append({"prompt":user_prompt,"raw":r.stdout})
    json.dump(RAWLOG,open(os.path.join(OUT,"raw_outputs.json"),"w"),ensure_ascii=False,indent=1)
    return extract_generation(r.stdout, full), round(time.time()-t0,1)
def coverage(text, kws):
    low=text.lower()
    hit=[k for k in kws if re.search(r"\b"+re.escape(k)+r"\b", low)]
    return len(hit)/len(kws), hit
def gen_prompt(kws):
    return "Write exactly one sentence that includes ALL of these words exactly as written: "+", ".join(kws)+". Write only the sentence, nothing else."
def fb_prompt(kws, draft):
    return ("Here is a writing task and a draft sentence.\nTask: Write exactly one sentence that includes ALL of these words exactly as written: "+", ".join(kws)+".\nDraft: "+draft+"\n\nGive specific, actionable feedback: list which of the required words are MISSING from the draft, and say exactly how to fix the sentence so it includes every required word. If no words are missing, say 'All required words are present.' Be brief.")
def refine_prompt(kws, draft, fb):
    return ("Task: Write exactly one sentence that includes ALL of these words exactly as written: "+", ".join(kws)+".\nDraft sentence: "+draft+"\nFeedback: "+fb+"\n\nNow write an improved version of the sentence that follows the feedback and includes every required word. Write only the improved sentence, nothing else.")
def chain(tid, kws):
    y0,t_gen=run(gen_prompt(kws),96)
    c0,hit0=coverage(y0,kws)
    fb,t_fb=run(fb_prompt(kws,y0),128)
    y1,t_rf=run(refine_prompt(kws,y0,fb),96)
    c1,hit1=coverage(y1,kws)
    return {"id":tid,"keywords":kws,"y0":y0,"y0_coverage":c0,"y0_hit":hit0,"feedback":fb,"y1":y1,"y1_coverage":c1,"y1_hit":hit1,"times_s":{"gen":t_gen,"fb":t_fb,"refine":t_rf}}
results=[]
for tid,kws in TASKS:
    row=chain(tid,kws)
    results.append(row)
    print(tid,"y0cov",row["y0_coverage"],"y1cov",row["y1_coverage"],flush=True)
    json.dump({"results":results},open(os.path.join(OUT,"results_incremental.json"),"w"),ensure_ascii=False,indent=1)
# stability: T1,T2 chain x2 more (total 3 runs incl. main)
stab=[]
for tid,kws in TASKS[:2]:
    runs=[]
    for i in range(2):
        row=chain(tid,kws)
        runs.append({"y0_coverage":row["y0_coverage"],"y1_coverage":row["y1_coverage"],"y0":row["y0"],"y1":row["y1"],"feedback":row["feedback"]})
        print("STAB",tid,i,row["y0_coverage"],row["y1_coverage"],flush=True)
    stab.append({"id":tid,"extra_runs":runs})
import statistics
m0=sum(r["y0_coverage"] for r in results)/len(results)*100
m1=sum(r["y1_coverage"] for r in results)/len(results)*100
full0=sum(1 for r in results if r["y0_coverage"]==1.0)
full1=sum(1 for r in results if r["y1_coverage"]==1.0)
summary={"mean_y0_coverage_pct":round(m0,1),"mean_y1_coverage_pct":round(m1,1),"full_success_y0":full0,"full_success_y1":full1,"n_tasks":len(results),"model":"Qwen2.5-1.5B-Instruct Q4_K_M","engine":"llama.cpp 0.9.0-dev build 1 commit 827466b","temp":0.0,"seed":42}
json.dump({"summary":summary,"results":results,"stability":stab},open(os.path.join(OUT,"results.json"),"w"),ensure_ascii=False,indent=1)
print(json.dumps(summary,ensure_ascii=False))

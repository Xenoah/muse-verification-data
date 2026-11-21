import pathlib, re, json, hashlib, collections
H=pathlib.Path.home()
base=H/"workspace/goals/note-10-000/hidden_files"
out={}
EMAIL=re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
DISC="有用性・満足は保証しない"
items=[
 ("1","2026-11-15","Self-Consistency","2203.11171","explainer-2026-11-15-self-consistency-draft.md",None),
 ("2","2026-11-16","Chain-of-Thought","2201.11903","explainer-2026-11-16-chain-of-thought-draft.md",None),
 ("3","2026-11-17","Zero-Shot CoT","2205.11916","explainer-2026-11-17-zero-shot-cot-draft.md","explainer-2026-11-17-zero-shot-cot-final.md"),
 ("4","2026-11-18","OPRO","2309.03409","explainer-2026-11-18-opro-draft.md","explainer-2026-11-18-opro-final.md"),
 ("5","2026-11-19","Self-Refine","2303.17651","explainer-2026-11-19-self-refine-draft.md","explainer-2026-11-19-self-refine-final.md"),
]
recs=[]
for num,date,topic,arxiv,df,ff in items:
    r={"number":num,"date":date,"topic":topic,"arxiv":arxiv}
    for kind,fn in (("draft",df),("final",ff)):
        if fn is None: r[kind]=None; continue
        p=base/fn; t=p.read_text(errors='ignore')
        r[kind]={"file":fn,"chars":len(t),"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()[:16],
                 "disclaimer_count":t.count(DISC),"md_headings":len(re.findall(r'^#{1,3} ',t,flags=re.M)),
                 "arxiv_found":arxiv in t,"email_count":len(EMAIL.findall(t))}
    if r["draft"] and r["final"]:
        r["draft_final_identical"]=r["draft"]["sha256"]==r["final"]["sha256"]
        r["final_minus_draft_chars"]=r["final"]["chars"]-r["draft"]["chars"]
    recs.append(r)
out["explainers"]=recs
# measurements
meas=[]
mdir=base/"explainer-measurements"
for d in sorted(mdir.iterdir()):
    if not d.is_dir(): continue
    fs=[f for f in d.rglob("*") if f.is_file()]
    meas.append({"date":d.name,"files":len(fs),"bytes":sum(f.stat().st_size for f in fs),
                 "names":sorted(f.name for f in fs),
                 "has_criteria":any(f.name.startswith("criteria") for f in fs),
                 "has_runlog":any(f.name=="run.log" for f in fs),
                 "has_runlog2":any(f.name=="run2.log" for f in fs),
                 "has_results_json":any(f.name.startswith("results") and f.suffix==".json" for f in fs),
                 "has_desk_check":any(f.name=="desk-check.md" for f in fs),
                 "has_measure_py":any(f.name.startswith("measure") and f.suffix==".py" for f in fs)})
out["measurements"]=meas
# reviews
rdir=base/"explainer-reviews"
rfs=sorted([f for f in rdir.iterdir() if f.is_file()])
out["reviews"]={"files":len(rfs),"bytes":sum(f.stat().st_size for f in rfs),"names":[f.name for f in rfs],
                "dates_covered":sorted(set(f.name[:10] for f in rfs))}
# covers
cdir=base/"covers"
cfs=sorted([f for f in cdir.iterdir() if f.is_file()])
out["covers"]={"files":len(cfs),"bytes":sum(f.stat().st_size for f in cfs),"names":[f.name for f in cfs]}
# pilot
pilot=H/"workspace/goals/note-10-000/files/pilot-explainer-001.md"
out["pilot"]={"exists":pilot.exists(),"chars":len(pilot.read_text(errors='ignore')) if pilot.exists() else 0}
# totals
allfiles=[base/fn for _,_,_,_,df,ff in items for fn in (df,ff) if fn]
out["summary"]={
 "explainer_files":len(allfiles),
 "drafts":sum(1 for r in recs if r["draft"]),
 "finals":sum(1 for r in recs if r["final"]),
 "finals_missing":[r["number"] for r in recs if not r["final"]],
 "identical_pairs":[r["number"] for r in recs if r.get("draft_final_identical")],
 "total_emails_in_manuscripts":sum((r["draft"]["email_count"] if r["draft"] else 0)+(r["final"]["email_count"] if r["final"] else 0) for r in recs),
 "measurement_days":len(meas),"measurement_files":sum(m["files"] for m in meas),"measurement_bytes":sum(m["bytes"] for m in meas),
 "review_files":out["reviews"]["files"],"cover_files":out["covers"]["files"],
}
print(json.dumps(out,ensure_ascii=False,indent=1))
(H/"workspace/goals/goal/hidden_files/audit-018/audit-018-results.json").write_text(json.dumps(out,ensure_ascii=False,indent=1))

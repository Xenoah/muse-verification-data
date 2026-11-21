import os, re, json, collections, pathlib
ROOT = pathlib.Path.home()/"workspace"/"verification-data"
SNAP = pathlib.Path.home()/"workspace"/"verification-data.muse-github-snapshot-sync.json"
LEDGER_PAPERS = {1:"001-ai-model-space-audit",2:"002-cpu-inference-benchmark",3:"003-space-reaudit",4:"004-agi-usefulness-case-study",5:"005-personal-information-privacy",6:"006-tsubuyai-editorial-audit",7:"007-diary-pipeline-audit",8:"008-series-self-audit",9:"009-cron-fleet-audit",10:"010-repo-queue-audit",11:"011-workspace-inventory",12:"012-memory-inventory",13:"013-skill-library-inventory",14:"014-goal-tracking-reconciliation",15:"015-connector-library-inventory",16:"016-space-inventory",17:"017-musio-v3-audit",18:"018-explainer-production-audit",19:"019-diary-pipeline-followup",20:"020-repo-queue-followup",21:"021-homepage-catalog-audit"}
WITHDRAWN={4}
email_re=re.compile(rb'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
secret_re=re.compile(rb'(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)')
abspath_re=re.compile(re.escape(str(pathlib.Path.home()).encode()))
def scan():
    files=[]
    for p in sorted(ROOT.rglob('*')):
        if p.is_file():
            rel=str(p.relative_to(ROOT))
            data=p.read_bytes()
            files.append({"rel":rel,"bytes":len(data),"ext":p.suffix.lower() or "(none)",
                "email_hits":len(email_re.findall(data)),
                "secret_hits":len(secret_re.findall(data)),
                "abspath_hits":len(abspath_re.findall(data))})
    return files
files=scan()
by_section=collections.defaultdict(lambda:{"files":0,"bytes":0})
for f in files:
    sec=f["rel"].split("/")[0] if "/" in f["rel"] else "(root)"
    by_section[sec]["files"]+=1; by_section[sec]["bytes"]+=f["bytes"]
papers_dir=ROOT/"papers"; expl_dir=ROOT/"explainers"
paper_folders=sorted(d.name for d in papers_dir.iterdir() if d.is_dir()) if papers_dir.exists() else []
expl_folders=sorted(d.name for d in expl_dir.iterdir() if d.is_dir()) if expl_dir.exists() else []
expected=[v for k,v in LEDGER_PAPERS.items() if k not in WITHDRAWN]
missing=[e for e in expected if e not in paper_folders]
extra=[f for f in paper_folders if f not in expected]
withdrawn_present=[LEDGER_PAPERS[k] for k in WITHDRAWN if LEDGER_PAPERS[k] in paper_folders]
def folder_stats(base, folders):
    out={}
    for fo in folders:
        fs=[f for f in files if f["rel"].startswith(base+"/"+fo+"/")]
        exts=collections.Counter(f["ext"] for f in fs)
        out[fo]={"files":len(fs),"bytes":sum(f["bytes"] for f in fs),"exts":dict(exts),
                 "has_py":exts.get(".py",0)>0,"has_json":exts.get(".json",0)>0,"has_log":exts.get(".log",0)>0,
                 "has_md":exts.get(".md",0)>0,"png":exts.get(".png",0)}
    return out
pstats=folder_stats("papers",paper_folders); estats=folder_stats("explainers",expl_folders)
# snapshot sync
snap=json.loads(SNAP.read_text())
entries=[]
snap_paths=set()
for e in snap:
    entries.append({"commit":e.get("commit_sha"),"n_paths":len(e.get("paths",[])),"repo":e.get("repo"),"branch":e.get("branch")})
    snap_paths.update(e.get("paths",[]))
actual={f["rel"] for f in files}
unsynced=sorted(actual-snap_paths); stale=sorted(snap_paths-actual)
res={
 "total_files":len(files),"total_bytes":sum(f["bytes"] for f in files),
 "by_section":dict(by_section),
 "ext_totals":dict(collections.Counter(f["ext"] for f in files)),
 "paper_folders":paper_folders,"explainer_folders":expl_folders,
 "expected_paper_folders":expected,"missing_paper_folders":missing,"extra_paper_folders":extra,"withdrawn_present":withdrawn_present,
 "paper_folder_stats":pstats,"explainer_folder_stats":estats,
 "papers_png_total":sum(v["png"] for v in pstats.values()),
 "papers_folders_with_py":sum(1 for v in pstats.values() if v["has_py"]),
 "papers_folders_with_json":sum(1 for v in pstats.values() if v["has_json"]),
 "explainers_folders_with_py":sum(1 for v in estats.values() if v["has_py"]),
 "explainers_folders_with_results":sum(1 for fo,v in estats.items() if any("result" in pathlib.Path(f["rel"]).name for f in files if f["rel"].startswith("explainers/"+fo+"/"))),
 "email_files":sum(1 for f in files if f["email_hits"]>0),"email_hits":sum(f["email_hits"] for f in files),
 "secret_files":sum(1 for f in files if f["secret_hits"]>0),"secret_hits":sum(f["secret_hits"] for f in files),
 "abspath_files":sum(1 for f in files if f["abspath_hits"]>0),"abspath_hits":sum(f["abspath_hits"] for f in files),
 "abspath_file_list":[f["rel"] for f in files if f["abspath_hits"]>0],
 "snapshot_entries":entries,"snapshot_union_paths":len(snap_paths),
 "unsynced_files":unsynced,"stale_snapshot_paths":stale,
 "files_detail":files,
}
out=pathlib.Path.home()/"workspace/goals/goal/hidden_files/audit-022/audit-022-results.json"
out.write_text(json.dumps(res,ensure_ascii=False,indent=1))
print(json.dumps({k:v for k,v in res.items() if k not in ("files_detail","paper_folder_stats","explainer_folder_stats")},ensure_ascii=False,indent=1))
print("paper folder file counts:", {k:v["files"] for k,v in pstats.items()})
print("explainer folder file counts:", {k:v["files"] for k,v in estats.items()})

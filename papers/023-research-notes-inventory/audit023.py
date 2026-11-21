import os, json, re, pathlib, collections
root=pathlib.Path.home()/"workspace/research_notes"
topics=sorted([p for p in root.iterdir() if p.is_dir()])
files=[]; per_topic=[]; errors=0
email_re=re.compile(rb'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
email_hits=0
for t in topics:
    tf=[p for p in t.rglob("*") if p.is_file()]
    rec={"topic":t.name,"file_count":len(tf),"bytes":sum(p.stat().st_size for p in tf),
         "has_report":(t/"report.md").exists(),"has_agents":(t/"AGENTS.md").exists(),
         "has_notes_dir":(t/"notes").is_dir(),
         "notes_files":len(list((t/"notes").glob("*"))) if (t/"notes").is_dir() else 0,
         "filenames":sorted(p.name for p in tf),
         "md_files":sum(1 for p in tf if p.suffix==".md")}
    per_topic.append(rec)
    for p in tf:
        try:
            data=p.read_bytes(); email_hits+=len(email_re.findall(data))
            files.append({"rel":str(p.relative_to(root)),"bytes":p.stat().st_size,"suffix":p.suffix})
        except Exception: errors+=1
total_bytes=sum(f["bytes"] for f in files)
reports=sum(1 for r in per_topic if r["has_report"])
agents=sum(1 for r in per_topic if r["has_agents"])
notes_dirs=sum(1 for r in per_topic if r["has_notes_dir"])
out={"root":str(root),"topics":len(topics),"files":len(files),"total_bytes":total_bytes,"errors":errors,
 "reports":reports,"agents_md":agents,"notes_dirs":notes_dirs,"email_pattern_hits_in_files":email_hits,
 "per_topic":per_topic,"all_files":files,
 "largest_topic":max(per_topic,key=lambda x:x["bytes"])["topic"],
 "topics_with_report_names":[r["topic"] for r in per_topic if r["has_report"]],
 "topics_without_report_names":[r["topic"] for r in per_topic if not r["has_report"]]}
pathlib.Path.home().joinpath("workspace/goals/goal/hidden_files/audit-023/audit-023-results.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False,indent=2))

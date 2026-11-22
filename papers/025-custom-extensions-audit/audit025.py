import pathlib, json, re, collections, sys
home=pathlib.Path.home()
roots={"custom_skills": home/"workspace/custom-skills", "custom_connectors": home/"workspace/custom-connectors"}
email_re=re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
def parse_simple_yaml(text):
    d={}
    for line in text.splitlines():
        m=re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if m: d[m.group(1)]=m.group(2).strip().strip('"').strip("'")
    return d
exts=[]; total_files=0; total_bytes=0; errors=0
for kind, root in roots.items():
    for d in sorted(root.iterdir()):
        if not d.is_dir(): continue
        files=[]; b=0; lines=0
        for f in sorted(d.rglob("*")):
            if f.is_file():
                try:
                    data=f.read_bytes(); b+=len(data)
                    try: lines+=data.decode("utf-8",errors="strict").count("\n")+ (1 if data else 0)
                    except: pass
                    files.append({"name":f.name,"rel":str(f.relative_to(d)),"bytes":len(data)})
                except Exception as e:
                    errors+=1
        total_files+=len(files); total_bytes+=b
        yaml_file = d/"skill.yaml" if kind=="custom_skills" else d/"connector.yaml"
        meta=parse_simple_yaml(yaml_file.read_text(errors="ignore")) if yaml_file.exists() else {}
        main = d/"SKILL.md" if kind=="custom_skills" else d/"CONNECTOR.md"
        exts.append({"kind":kind,"name":d.name,"files":files,"file_count":len(files),"bytes":b,"lines_approx":lines,
                     "has_main_doc": main.exists(),"has_yaml": yaml_file.exists(),
                     "include_in_prompt_raw": meta.get("include_in_prompt"),
                     "category": meta.get("category"), "title": meta.get("title") or meta.get("id"),
                     "has_bin": (d/"bin").exists(),
                     "extra_files":[f["rel"] for f in files if f["name"] not in ("SKILL.md","CONNECTOR.md","skill.yaml","connector.yaml",".write-lock")]})
# prompt-injected learned skills as observed in this run's injected context (recorded manually, verifiable against run context)
injected_learned=["supplied_asset_video","note_article_structure_check","resilient_long_downloads"]
injected_connectors=["custom.openai"]
for e in exts:
    e["in_injected_list"]= (e["name"] in injected_learned) if e["kind"]=="custom_skills" else (e["name"] in injected_connectors)
skills=[e for e in exts if e["kind"]=="custom_skills"]; conns=[e for e in exts if e["kind"]=="custom_connectors"]
summary={
 "total_extensions": len(exts), "skills": len(skills), "connectors": len(conns),
 "total_files": total_files, "total_bytes": total_bytes, "read_errors": errors,
 "skill_bytes": sum(e["bytes"] for e in skills), "connector_bytes": sum(e["bytes"] for e in conns),
 "skills_in_injected": sum(1 for e in skills if e["in_injected_list"]),
 "skills_not_in_injected": [e["name"] for e in skills if not e["in_injected_list"]],
 "include_true": [e["name"] for e in exts if e["include_in_prompt_raw"]=="true"],
 "include_false": [e["name"] for e in exts if e["include_in_prompt_raw"]=="false"],
 "include_unset": [e["name"] for e in exts if e["include_in_prompt_raw"] not in ("true","false")],
 "all_have_main_and_yaml": all(e["has_main_doc"] and e["has_yaml"] for e in exts),
 "categories": dict(collections.Counter(e["category"] for e in skills if e["category"])),
 "email_hits_in_main_docs": None,
}
# email scan over all files (count only, no strings)
hits=0; hitfiles=0
for kind, root in roots.items():
    for f in root.rglob("*"):
        if f.is_file():
            t=f.read_bytes().decode("utf-8",errors="ignore")
            c=len(email_re.findall(t))
            if c: hitfiles+=1; hits+=c
summary["email_hits"]=hits; summary["email_hit_files"]=hitfiles
out={"summary":summary,"extensions":exts,"injected_learned_skills":injected_learned,"injected_custom_connectors":injected_connectors}
pathlib.Path(sys.argv[1]).write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))

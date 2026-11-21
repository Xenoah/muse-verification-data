import json, re, os, statistics, collections, datetime, urllib.parse
ROOT="~/workspace/tsubuyai-tech-work"
def parse(path):
    t=open(path,encoding="utf-8").read()
    m=re.match(r"^# ([^\n]+)\n\s*```json\n([\s\S]*?)\n```\n([\s\S]*)$", t)
    if not m: return None
    return {"headline_line":m.group(1), "meta":json.loads(m.group(2)), "body":m.group(3).strip(), "file":os.path.basename(path)}
agents={}
for f in sorted(os.listdir(f"{ROOT}/agents")):
    p=parse(f"{ROOT}/agents/{f}")
    agents[p["meta"]["id"]]=p["meta"]
posts=[parse(f"{ROOT}/content/posts/{f}") for f in sorted(os.listdir(f"{ROOT}/content/posts")) if f.endswith(".md")]
feats=[parse(f"{ROOT}/content/features/{f}") for f in sorted(os.listdir(f"{ROOT}/content/features")) if f.endswith(".md")]
def cp(s): return len(s)
out={}
out["commit"]="77c661c"
out["counts"]={"posts":len(posts),"features":len(feats),"total":len(posts)+len(feats),
 "posts_by_author":dict(collections.Counter(p["meta"]["author"] for p in posts)),
 "posts_by_status":dict(collections.Counter(p["meta"]["status"] for p in posts)),
 "posts_by_kind":dict(collections.Counter(p["meta"]["kind"] for p in posts)),
 "features_by_author":dict(collections.Counter(p["meta"]["author"] for p in feats))}
allitems=posts+feats
# sources
src_total=sum(len(p["meta"]["sources"]) for p in allitems)
prim_items=sum(1 for p in allitems if any(s["type"]=="primary" for s in p["meta"]["sources"]))
out["sources"]={"total_sources":src_total,
 "type_counts":dict(collections.Counter(s["type"] for p in allitems for s in p["meta"]["sources"])),
 "items_with_primary":prim_items,
 "items_sources_count_dist":dict(collections.Counter(len(p["meta"]["sources"]) for p in allitems)),
 "distinct_hosts":sorted(set(urllib.parse.urlparse(s["url"]).hostname for p in allitems for s in p["meta"]["sources"]))}
# allowed domain check
viol_dom=[]
for p in allitems:
    allowed=agents[p["meta"]["author"]]["allowedDomains"]
    for s in p["meta"]["sources"]:
        h=urllib.parse.urlparse(s["url"]).hostname
        if not any(h==d or h.endswith("."+d) for d in allowed): viol_dom.append((p["meta"]["id"],h))
out["sources"]["domain_violations"]=viol_dom
# duplicate primary urls
prim_urls=[s["url"].rstrip("/") for p in posts for s in p["meta"]["sources"] if s["type"]=="primary"]
out["duplicates"]={"post_ids_dup":[k for k,v in collections.Counter(p["meta"]["id"] for p in allitems).items() if v>1],
 "primary_url_dup":[k for k,v in collections.Counter(prim_urls).items() if v>1],
 "primary_url_total_posts":len(prim_urls)}
# body lengths
pl=[cp(p["body"]) for p in posts]; fl=[cp(f["body"]) for f in feats]
out["body"]={"post_len_min":min(pl),"post_len_max":max(pl),"post_len_median":statistics.median(pl),
 "posts_over_300":sum(1 for x in pl if x>300),"posts_over_2000":sum(1 for x in pl if x>2000),"posts_under_30":sum(1 for x in pl if x<30),
 "posts_over_author_max":sum(1 for p in posts if cp(p["body"])>agents[p["meta"]["author"]]["maxSummaryChars"]),
 "feature_len_min":min(fl),"feature_len_max":max(fl),"feature_lengths":fl,
 "features_outside_800_12000":sum(1 for x in fl if x<800 or x>12000)}
# forbidden patterns in body
pat=re.compile(r"!\[|https?://|```|^#{1,6} ",re.M)
out["body"]["posts_forbidden_pattern"]=[p["meta"]["id"] for p in posts if pat.search(p["body"])]
out["body"]["features_forbidden_pattern"]=[p["meta"]["id"] for p in feats if pat.search(p["body"])]
out["body"]["features_without_paragraph_break"]=[f["meta"]["id"] for f in feats if "\n\n" not in f["body"]]
# headline
out["headline"]={"mismatch_line_vs_meta":[p["meta"]["id"] for p in allitems if p["headline_line"]!=p["meta"]["headline"]],
 "outside_8_72":[p["meta"]["id"] for p in allitems if not (8<=cp(p["meta"]["headline"])<=72)],
 "filename_id_mismatch":[p["file"] for p in allitems if p["file"][:-3]!=p["meta"]["id"]]}
# dates age
def dparse(s): return datetime.datetime.fromisoformat(s.replace("Z","+00:00"))
age_viol=[]; ages=[]
for p in allitems:
    sd=datetime.datetime.fromisoformat(p["meta"]["sourceDate"]+"T00:00:00+09:00")
    pub=dparse(p["meta"]["publishedAt"]); age=(pub-sd).total_seconds()/86400; ages.append(round(age,2))
    if age<0 or age>(agents[p["meta"]["author"]]["maxAgeDays"]+1): age_viol.append((p["meta"]["id"],round(age,2)))
out["dates"]={"age_days_min":min(ages),"age_days_max":max(ages),"age_violations":age_viol,"ages":ages,
 "published_range":[min(p["meta"]["publishedAt"] for p in allitems), max(p["meta"]["publishedAt"] for p in allitems)]}
# review
out["review"]={"all_checks_true_items":sum(1 for p in allitems if all(p["meta"]["review"]["checks"].values())),
 "checks_keys_ok":sum(1 for p in allitems if set(p["meta"]["review"]["checks"])=={"primaryRead","dateChecked","claimsSupported","notMisleading","noNegativeFocus","rightsChecked","rulesRead"}),
 "evidence_scope":dict(collections.Counter(p["meta"]["review"]["evidenceScope"] for p in allitems)),
 "reviewers":dict(collections.Counter(p["meta"]["review"]["reviewer"] for p in allitems)),
 "rights_values":dict(collections.Counter(p["meta"]["review"]["rights"] for p in allitems)),
 "items_with_independent_source_when_corrob":sum(1 for p in allitems if p["meta"]["review"]["evidenceScope"]=="independently-corroborated" and any(s["type"]=="independent" for s in p["meta"]["sources"]))}
# timing 72h
tim_viol=[]
for p in allitems:
    pub=dparse(p["meta"]["publishedAt"])
    if p["meta"]["corrections"]: pub=max(pub, max(dparse(c["date"]) for c in p["meta"]["corrections"]))
    rev=dparse(p["meta"]["review"]["reviewedAt"])
    if any(dparse(s["checkedAt"])>rev for s in p["meta"]["sources"]): tim_viol.append((p["meta"]["id"],"checked_after_review"))
    if (pub-rev).total_seconds()>72*3600 or (pub-rev).total_seconds()<-300: tim_viol.append((p["meta"]["id"],"review_outside_72h"))
    for s in p["meta"]["sources"]:
        if (pub-dparse(s["checkedAt"])).total_seconds()>72*3600: tim_viol.append((p["meta"]["id"],"checked_outside_72h"))
out["review"]["timing_violations"]=tim_viol
# corrections / tags
out["misc"]={"corrections_nonempty":sum(1 for p in allitems if p["meta"]["corrections"]),
 "tags_outside_1_5":[p["meta"]["id"] for p in allitems if not (1<=len(p["meta"]["tags"])<=5)],
 "sources_outside_1_4":[p["meta"]["id"] for p in allitems if not (1<=len(p["meta"]["sources"])<=4)]}
# features linkage
postmap={p["meta"]["id"]:p for p in posts}
link=[]
for f in feats:
    lp=postmap.get(f["meta"].get("postId"))
    link.append({"feature":f["meta"]["id"],"postId":f["meta"].get("postId"),"exists":lp is not None,
      "same_author": (lp["meta"]["author"]==f["meta"]["author"]) if lp else False,
      "feature_after_post": (dparse(f["meta"]["publishedAt"])>=dparse(lp["meta"]["publishedAt"])) if lp else False})
out["features_linkage"]=link
out["features_per_post_dup"]=[k for k,v in collections.Counter(f["meta"].get("postId") for f in feats).items() if v>1]
# AI-model subset (2026-11-12 migration posts)
mig=[p for p in posts if p["meta"]["id"].startswith("20261112-")]
out["migration_20261112"]={"count":len(mig),"ids":[p["meta"]["id"] for p in mig],
 "all_have_primary":all(any(s["type"]=="primary" for s in p["meta"]["sources"]) for p in mig),
 "reviewers":dict(collections.Counter(p["meta"]["review"]["reviewer"] for p in mig))}
print(json.dumps(out,ensure_ascii=False,indent=1))
open("~/workspace/goals/goal/hidden_files/audit-006/audit-006-results.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))

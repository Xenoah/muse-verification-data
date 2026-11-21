import json, collections, re, pathlib
src = pathlib.Path.home()/"workspace/agents/f0910df9-1a15-4d79-9a65-61cef641841a/tool-output/artifact.invoke_action-call_01a1de63cb0e72e3a393557348d2e9ad.json"
raw=json.loads(src.read_text())
data=raw["data"]
repos=data["repos"]
counts=data["counts"]
sync=data["sync"]
def pct(n,d): return round(n/d*100,1) if d else 0
langs=collections.Counter(r.get("language") or "(none)" for r in repos)
status=collections.Counter(r["status"] for r in repos)
desc_missing=sum(1 for r in repos if not r.get("description"))
desc_present=len(repos)-desc_missing
topics_any=sum(1 for r in repos if r.get("topics"))
stars=sum(r.get("stars") or 0 for r in repos)
forks=sum(r.get("forks") or 0 for r in repos)
issues=sum(r.get("openIssues") or 0 for r in repos)
archived=sum(1 for r in repos if r.get("isArchived"))
isfork=sum(1 for r in repos if r.get("isFork"))
private=sum(1 for r in repos if r.get("isPrivate"))
manual=sum(1 for r in repos if r.get("manual"))
created_years=collections.Counter((r.get("repoCreatedAt") or "")[:4] for r in repos)
updated_dates=sorted(r.get("repoUpdatedAt") or "" for r in repos)
# email check in descriptions/titles
text=json.dumps(repos, ensure_ascii=False)
emails=len(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))
done=[r for r in repos if r["status"]=="done"]
done_names=[r["fullName"] for r in done]
# article body lengths for done
done_info=[{"fullName":r["fullName"],"title":r.get("articleTitle"),"body_chars":len(r.get("articleBody") or ""),"sources_lines":len((r.get("articleSources") or "").splitlines()) if r.get("articleSources") else 0} for r in done]
# updated in Nov 2026 etc
nov_updated=sum(1 for r in repos if (r.get("repoUpdatedAt") or "").startswith("2026-11"))
res={
 "counts_from_space":counts,"sync":sync,"total_parsed":len(repos),
 "status_counter":dict(status),
 "done_pct":pct(status.get("done",0),len(repos)),
 "pending_pct":pct(status.get("pending",0),len(repos)),
 "remaining_days_at_1_per_day":status.get("pending",0)+status.get("draft",0)+status.get("editing",0),
 "languages":langs.most_common(),
 "language_distinct":len(langs),
 "desc_present":desc_present,"desc_missing":desc_missing,"desc_present_pct":pct(desc_present,len(repos)),
 "topics_any":topics_any,"topics_none":len(repos)-topics_any,
 "stars_total":stars,"forks_total":forks,"open_issues_total":issues,
 "archived":archived,"is_fork":isfork,"is_private":private,"manual":manual,
 "created_years":dict(sorted(created_years.items())),
 "updated_min":updated_dates[0],"updated_max":updated_dates[-1],
 "nov2026_updated":nov_updated,
 "emails_in_queue_data":emails,
 "done_info":done_info,
}
out=pathlib.Path.home()/"workspace/goals/goal/hidden_files/audit-010/audit-010-results.json"
out.write_text(json.dumps(res,ensure_ascii=False,indent=2))
print(json.dumps(res,ensure_ascii=False,indent=2))

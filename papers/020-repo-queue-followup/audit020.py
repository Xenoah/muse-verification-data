import json, collections, re, pathlib, datetime
base = pathlib.Path.home()/"workspace/goals/goal/hidden_files/audit-020"
cur_raw = json.loads((base/"listrepos-raw.json").read_text())
old_raw = json.loads((base/"listrepos-010-baseline-raw.json").read_text())
old_res = json.loads((pathlib.Path.home()/"workspace/goals/goal/hidden_files/audit-010/audit-010-results.json").read_text())
repos = cur_raw["data"]["repos"]; counts = cur_raw["data"]["counts"]; sync = cur_raw["data"]["sync"]
old_repos = old_raw["data"]["repos"]
def pct(n,d): return round(n/d*100,1) if d else 0
langs = collections.Counter(r.get("language") or "(none)" for r in repos)
status = collections.Counter(r["status"] for r in repos)
desc_missing = sum(1 for r in repos if not r.get("description"))
topics_any = sum(1 for r in repos if r.get("topics"))
stars = sum(r.get("stars") or 0 for r in repos); forks = sum(r.get("forks") or 0 for r in repos)
issues = sum(r.get("openIssues") or 0 for r in repos)
created_years = collections.Counter((r.get("repoCreatedAt") or "")[:4] for r in repos)
updated_dates = sorted(r.get("repoUpdatedAt") or "" for r in repos)
text = json.dumps(repos, ensure_ascii=False)
emails = len(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))
done = [r for r in repos if r["status"]=="done"]
done_info = [{"fullName": r["fullName"], "title": r.get("articleTitle"), "body_chars": len(r.get("articleBody") or ""), "sources_lines": len((r.get("articleSources") or "").splitlines()) if r.get("articleSources") else 0, "articleUpdatedAt": r.get("articleUpdatedAt"), "isPrivate": r.get("isPrivate")} for r in sorted(done, key=lambda r: r.get("articleUpdatedAt") or "")]
# set comparison vs 010 snapshot
old_by = {r["fullName"]: r for r in old_repos}; cur_by = {r["fullName"]: r for r in repos}
added = sorted(set(cur_by)-set(old_by)); removed = sorted(set(old_by)-set(cur_by)); common = sorted(set(cur_by)&set(old_by))
transitions = collections.Counter((old_by[n]["status"], cur_by[n]["status"]) for n in common)
new_done_common = [n for n in common if old_by[n]["status"]!="done" and cur_by[n]["status"]=="done"]
added_info = [{"fullName": n, "isPrivate": cur_by[n].get("isPrivate"), "manual": cur_by[n].get("manual"), "repoCreatedAt": cur_by[n].get("repoCreatedAt"), "status": cur_by[n]["status"], "language": cur_by[n].get("language")} for n in added]
added_private = sum(1 for n in added if cur_by[n].get("isPrivate"))
added_created_after_1115 = sum(1 for n in added if (cur_by[n].get("repoCreatedAt") or "") >= "2026-11-15")
added_created_before = len(added)-added_created_after_1115
# anomalies
pending_with_body = [{"fullName": r["fullName"], "body_chars": len(r.get("articleBody") or ""), "has_title": bool(r.get("articleTitle")), "draftError": (r.get("draftError") or "")[:120]} for r in repos if r["status"]=="pending" and r.get("articleBody")]
draft_error = [{"fullName": r["fullName"], "status": r["status"]} for r in repos if r.get("draftError")]
done_private = [r["fullName"] for r in done if r.get("isPrivate")]
private_all = [r["fullName"] for r in repos if r.get("isPrivate")]
# projection: remaining = pending+draft+editing; 1/day starting 2026-11-21 (day 1 = 2026-11-21)
remaining = status.get("pending",0)+status.get("draft",0)+status.get("editing",0)
start = datetime.date(2026,11,21)
finish = start + datetime.timedelta(days=remaining-1)
old_remaining = old_res["remaining_days_at_1_per_day"]
# elapsed days between syncs: 2026-11-15T00:50Z -> 2026-11-20T00:51Z = 5 days
res = {
 "counts_from_space": counts, "sync": sync, "total_parsed": len(repos),
 "status_counter": dict(status), "done_pct": pct(status.get("done",0), len(repos)), "pending_pct": pct(status.get("pending",0), len(repos)),
 "remaining_days_at_1_per_day": remaining, "projection_start": str(start), "projection_finish": str(finish),
 "languages": langs.most_common(), "language_distinct": len(langs),
 "desc_present": len(repos)-desc_missing, "desc_missing": desc_missing, "desc_present_pct": pct(len(repos)-desc_missing, len(repos)),
 "topics_any": topics_any, "topics_none": len(repos)-topics_any,
 "stars_total": stars, "forks_total": forks, "open_issues_total": issues,
 "archived": sum(1 for r in repos if r.get("isArchived")), "is_fork": sum(1 for r in repos if r.get("isFork")),
 "is_private": sum(1 for r in repos if r.get("isPrivate")), "manual": sum(1 for r in repos if r.get("manual")),
 "created_years": dict(sorted(created_years.items())), "updated_min": updated_dates[0], "updated_max": updated_dates[-1],
 "nov2026_updated": sum(1 for r in repos if (r.get("repoUpdatedAt") or "").startswith("2026-11")),
 "emails_in_queue_data": emails, "done_info": done_info,
 "vs_010": {"old_total": old_res["total_parsed"], "old_done": old_res["status_counter"].get("done"), "old_pending": old_res["status_counter"].get("pending"), "old_remaining": old_remaining, "old_projection_finish_reported": "2027-02-07",
   "added_count": len(added), "removed_count": len(removed), "removed": removed, "added": added_info,
   "added_private": added_private, "added_created_on_or_after_2026-11-15": added_created_after_1115, "added_created_before_2026-11-15": added_created_before,
   "transitions": {f"{a}->{b}": c for (a,b),c in sorted(transitions.items())}, "new_done_among_common": new_done_common},
 "anomalies": {"pending_with_article_body": pending_with_body, "draft_error_entries": draft_error, "done_private": done_private, "private_all": private_all},
}
out = base/"audit-020-results.json"
out.write_text(json.dumps(res, ensure_ascii=False, indent=2))
print(json.dumps(res, ensure_ascii=False, indent=2))

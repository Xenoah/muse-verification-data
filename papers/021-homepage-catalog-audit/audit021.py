#!/usr/bin/env python3
"""Paper 021: full audit of Xenoah.github.io project catalog (data/projects.json, 108 entries).
Read-only: parses projects.json, checks field rules from docs/ADDING_PROJECTS.md,
reconciles generated artefacts (projects.htm count line, sitemap, menu includes) by counting,
and cross-checks distinct GitHub repos referenced. No network, no writes outside results JSON.
"""
import json, re, collections, pathlib, statistics, sys
from urllib.parse import urlparse

ROOT = pathlib.Path.home() / "workspace/xenoah-github-io"
OUT = pathlib.Path.home() / "workspace/goals/goal/hidden_files/audit-021/audit-021-results.json"

data = json.loads((ROOT / "data/projects.json").read_text(encoding="utf-8"))
assert isinstance(data, list)
total = len(data)

ALLOWED_CATS = ["music","images","tools","games","learn","data","models","software","community"]
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

ids = [e.get("id") for e in data]
titles = [e.get("title") for e in data]
cats = collections.Counter(e.get("category") for e in data)

pages_present = [e for e in data if e.get("pagesUrl")]
pages_null = [e for e in data if not e.get("pagesUrl")]
# sourceOnlyReason compliance: required when pagesUrl is null (ADDING_PROJECTS.md)
null_with_reason = [e for e in pages_null if e.get("sourceOnlyReason")]
null_without_reason = [e for e in pages_null if not e.get("sourceOnlyReason")]
reasons = collections.Counter(e.get("sourceOnlyReason") for e in null_with_reason)

src_present = [e for e in data if e.get("sourceUrl")]
src_missing = [e for e in data if not e.get("sourceUrl")]

def repo_of(url):
    if not url: return None
    p = urlparse(url)
    parts = [x for x in p.path.split("/") if x]
    if len(parts) >= 2 and p.netloc == "github.com":
        return f"{parts[0]}/{parts[1]}"
    return None

repos = collections.Counter()
in_site = 0
external_entries = 0
for e in data:
    r = repo_of(e.get("sourceUrl"))
    if r: repos[r] += 1
    if e.get("sourceUrl") and "/Xenoah.github.io/" in e.get("sourceUrl"):
        in_site += 1
    elif r and r != "Xenoah/Xenoah.github.io":
        external_entries += 1

distinct_repos = sorted(repos.keys())
distinct_external_repos = [r for r in distinct_repos if r != "Xenoah/Xenoah.github.io"]

pages_urls = [e.get("pagesUrl") for e in pages_present]
pages_dup = [u for u,c in collections.Counter(pages_urls).items() if c>1]
src_urls = [e.get("sourceUrl") for e in src_present]
src_dup_counts = collections.Counter(src_urls)
src_dup = {u:c for u,c in src_dup_counts.items() if c>1}

updated_present = [e for e in data if e.get("updated")]
updated_vals = sorted(e["updated"] for e in updated_present)
featured = [e for e in data if e.get("featured") is True]
thumb = [e for e in data if e.get("thumbnailSlug")]
pending = [e for e in data if e.get("pendingPagesUrl")]

desc_lens = [len(e.get("description") or "") for e in data]
title_lens = [len(e.get("title") or "") for e in data]

field_keys = collections.Counter()
for e in data:
    for k in e.keys(): field_keys[k]+=1

invalid_cats = [e["id"] for e in data if e.get("category") not in ALLOWED_CATS]
invalid_ids = [i for i in ids if not i or not ID_RE.match(i)]
non_https_pages = [e["id"] for e in pages_present if not str(e["pagesUrl"]).startswith("https://")]
non_https_src = [e["id"] for e in src_present if not str(e.get("sourceUrl")).startswith("https://")]
future_updated = [e["id"] for e in updated_present if e["updated"] > "2026-11-21"]

emails = EMAIL_RE.findall((ROOT/"data/projects.json").read_text(encoding="utf-8"))

# Generated artefacts reconciliation (text counts only)
projects_htm = (ROOT/"projects.htm").read_text(encoding="utf-8", errors="replace")
m = re.search(r"(\d+)\s*件", projects_htm)
projects_htm_count = int(m.group(1)) if m else None
# count occurrences of each id in generated includes + sitemap
gen_files = {}
for rel in ["_includes/site_menu.html","sitemap.xml","sitemap.htm"]:
    p = ROOT/rel
    if p.exists():
        txt = p.read_text(encoding="utf-8", errors="replace")
        gen_files[rel] = {"bytes": len(txt.encode()), "ids_found": sum(1 for i in ids if i and i in txt),
                          "pages_urls_found": sum(1 for u in pages_urls if u and u in txt)}
# Generated include reconciliation (exact counts)
def _read(rel):
    p = ROOT/rel
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
_cat = _read("_includes/project_catalog.html")
_menu = _read("_includes/site_menu.html")
_feat = _read("_includes/featured_projects.html")
_sm = _read("sitemap.xml")
generated_reconciliation = {
  "catalog_articles": _cat.count("<article"),
  "catalog_titles_found": sum(1 for e in data if e.get("title") and e["title"] in _cat),
  "catalog_source_urls_found": sum(1 for e in data if e.get("sourceUrl") and e["sourceUrl"] in _cat),
  "menu_titles_found": sum(1 for e in data if e.get("title") and e["title"] in _menu),
  "featured_titles_found": sum(1 for e in data if e.get("featured") is True and e["title"] in _feat),
  "sitemap_pages_urls_found": sum(1 for e in data if e.get("pagesUrl") and e["pagesUrl"] in _sm),
}
# changelog mention of catalog expansion
changelog = (ROOT/"changelog.htm").read_text(encoding="utf-8", errors="replace")

preparing_ids = sorted(e["id"] for e in pages_null if e.get("sourceOnlyReason") == "公開サイト準備中（現在はGitHubで参照）")
pending_ids = sorted(e["id"] for e in data if e.get("pendingPagesUrl"))
desc_min = min(desc_lens)
desc_min_entries = [{"id": e["id"], "description": e.get("description")} for e in data if len(e.get("description") or "") == desc_min]

results = {
  "total": total,
  "unique_ids": len(set(ids)), "dup_ids": [i for i,c in collections.Counter(ids).items() if c>1],
  "unique_titles": len(set(titles)), "dup_titles": [t for t,c in collections.Counter(titles).items() if c>1],
  "categories": cats.most_common(), "category_distinct": len(cats),
  "invalid_categories": invalid_cats, "invalid_ids": invalid_ids,
  "pages_present": len(pages_present), "pages_null": len(pages_null),
  "pages_present_pct": round(len(pages_present)/total*100,2),
  "null_with_reason": len(null_with_reason), "null_without_reason_ids": [e["id"] for e in null_without_reason],
  "source_only_reasons_top": reasons.most_common(10),
  "source_only_reasons_distinct": len(reasons),
  "src_present": len(src_present), "src_missing_ids": [e["id"] for e in src_missing],
  "distinct_repos_referenced": len(distinct_repos),
  "distinct_external_repos": len(distinct_external_repos),
  "in_site_entries": in_site, "external_repo_entries": external_entries,
  "self_repo_entries": repos.get("Xenoah/Xenoah.github.io",0),
  "pages_dup": pages_dup, "src_dup_distinct_urls": len(src_dup), "src_dup_total_entries": sum(src_dup.values()),
  "updated_present": len(updated_present), "updated_missing": total-len(updated_present),
  "updated_min": updated_vals[0] if updated_vals else None, "updated_max": updated_vals[-1] if updated_vals else None,
  "updated_future_ids": future_updated,
  "featured": len(featured), "featured_ids": [e["id"] for e in featured],
  "thumbnail_slug": len(thumb), "pending_pages_url": len(pending),
  "desc_len_min": min(desc_lens), "desc_len_max": max(desc_lens), "desc_len_median": statistics.median(desc_lens),
  "desc_missing": sum(1 for e in data if not e.get("description")),
  "title_missing": sum(1 for e in data if not e.get("title")),
  "field_keys": field_keys.most_common(),
  "non_https_pages": non_https_pages, "non_https_src": non_https_src,
  "emails_in_projects_json": len(emails),
  "projects_htm_count_line": projects_htm_count,
  "generated_files": gen_files,
  "generated_reconciliation": generated_reconciliation,
  "preparing_reason_ids": preparing_ids,
  "pending_pages_ids": pending_ids,
  "preparing_equals_pending": preparing_ids == pending_ids,
  "desc_min_entries": desc_min_entries,
  "gate_checks": "gate-check-output.txt (build-projects.js --check exit 0; check-site.js exit 0, SEO 54 pages OK; run twice with same result)",
  "pages_null_by_category": collections.Counter(e.get("category") for e in pages_null).most_common(),
  "pages_present_by_category": collections.Counter(e.get("category") for e in pages_present).most_common(),
  "external_repos_list": distinct_external_repos,
}
OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(results, ensure_ascii=False, indent=2))

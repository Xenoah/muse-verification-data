#!/usr/bin/env python3
"""Paper 019 audit: diary pipeline longitudinal follow-up. Read-only."""
import json, os, re

REPO = os.path.expanduser("~/workspace/x-note-collector-repo/x-note-collector-main")
STATES = os.path.expanduser("~/workspace/goals/x-note-collector/hidden_files")
BLOG = os.path.expanduser("~/workspace/xenoah-github-io/blog/articles")
OLD = [f"2026-11-{d:02d}" for d in range(6, 14)]
NEW = [f"2026-11-{d:02d}" for d in range(14, 20)]
ALL = OLD + NEW
PREFIX = "【X日記】"
TITLE_RE = re.compile(r"^(?:【X日記】)?(\d{4}-\d{2}-\d{2}) (.+) ― (.+)$")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def num(s):
    return int(s.replace(",", "")) if s else None

def parse_day(date):
    d = {"date": date}
    pkg = os.path.join(REPO, "articles", date)
    aj = json.load(open(os.path.join(pkg, "article.json")))
    cj = json.load(open(os.path.join(pkg, "checks.json")))
    pj = json.load(open(os.path.join(pkg, "publication.json")))
    d["title"] = aj["title"]
    d["prefix_xnikki"] = aj["title"].startswith(PREFIX)
    m = TITLE_RE.match(aj["title"])
    d["title_core_ok"] = bool(m) and m.group(1) == date
    d["highlight_bracketed"] = bool(m) and m.group(3).startswith("「") and m.group(3).endswith("」")
    d["highlight_raw"] = m.group(3) if m else None
    d["highlight_contains_brackets"] = bool(m) and ("「" in m.group(3) and "」" in m.group(3))
    d["tags_count"] = len(aj["tags"])
    d["source_urls_count"] = len(aj["source_urls"])
    d["checks_source_count"] = cj["source_count"]
    d["checks_match"] = cj["source_count"] == len(aj["source_urls"])
    d["checks_url_check"] = cj["source_url_check"]
    d["checks_copy_screen"] = cj["source_copy_screen"]
    d["package_publication_status"] = pj["status"]
    body_path = os.path.join(pkg, "body.md")
    d["body_bytes_disk"] = os.path.getsize(body_path)
    body_txt = open(body_path, encoding="utf-8", errors="replace").read()
    d["body_email_pattern_count"] = len(EMAIL_RE.findall(body_txt))
    cover = os.path.join(pkg, "cover.webp")
    d["cover_webp_bytes_disk"] = os.path.getsize(cover) if os.path.exists(cover) else None
    bdir = os.path.join(BLOG, f"{date}-diary")
    if os.path.isdir(bdir):
        files = sorted(os.listdir(bdir))
        webps = [f for f in files if f.endswith(".webp")]
        d["blog_files"] = files
        d["blog_image_bytes"] = sum(os.path.getsize(os.path.join(bdir, f)) for f in webps)
        d["blog_index_bytes"] = os.path.getsize(os.path.join(bdir, "index.html")) if "index.html" in files else None
        d["blog_total_bytes"] = d["blog_image_bytes"] + (d["blog_index_bytes"] or 0)
    else:
        d["blog_files"] = []
    txt = open(os.path.join(STATES, f"{date}-run-state.md"), encoding="utf-8").read()
    d["runstate_chars"] = len(txt)
    m = re.search(r"posts_received (\d+), posts_included (\d+)", txt)
    if m:
        d["received"], d["included"] = int(m.group(1)), int(m.group(2))
    else:
        m = re.search(r"Received (\d+), (?:eligible|included) (\d+)", txt)
        if m:
            d["received"], d["included"] = int(m.group(1)), int(m.group(2))
    m = re.search(r"body\.md ([\d,]+) bytes; (\d+) considered / (\d+) adopted", txt)
    if m:
        d["body_bytes_reported"] = num(m.group(1)); d["considered"] = int(m.group(2)); d["adopted"] = int(m.group(3))
    else:
        m = re.search(r"body\.md ([\d,]+) bytes\. (\d+) adopted / (\d+) considered", txt)
        if m:
            d["body_bytes_reported"] = num(m.group(1)); d["adopted"] = int(m.group(2)); d["considered"] = int(m.group(3))
        else:
            m = re.search(r"(\d+) considered / (\d+) adopted", txt)
            if m:
                d["considered"] = int(m.group(1)); d["adopted"] = int(m.group(2))
            m2 = re.search(r"body\.md ([\d,]+) bytes", txt)
            if m2:
                d["body_bytes_reported"] = num(m2.group(1))
    m = re.search(r"animated WebP ([\d,]+) bytes", txt)
    if m:
        d["cover_webp_bytes_reported"] = num(m.group(1))
    m = re.search(r"GIF ([\d,]+) bytes", txt)
    if m:
        d["cover_gif_bytes"] = num(m.group(1))
    m = re.search(r"TOTAL ([\d,]+) bytes", txt)
    if m:
        d["day_total_reported"] = num(m.group(1))
    else:
        m = re.search(r"Day total ([\d,]+) bytes", txt)
        if m:
            d["day_total_reported"] = num(m.group(1))
    d["note_urls"] = sorted(set(re.findall(r"https://note\.com/xenoah_memo/n/[a-z0-9]+", txt)))
    d["run_complete_marker"] = bool(re.search(r"RUN COMPLETE|COMPLETE end-to-end|run is COMPLETE", txt))
    d["persona_claim"] = "persona" in txt
    m = re.search(r"AI-model corner:?\s*(INCLUDED|OMITTED|NONE|YES)", txt)
    if m:
        d["ai_corner"] = m.group(1)
    d["gif_issue_mentioned"] = bool(re.search(r"body-top GIF (missing|INSERTED|insertion failed|failed)", txt))
    return d

def agg(days):
    a = {}
    a["days"] = len(days)
    a["received_total"] = sum(d.get("received", 0) for d in days)
    a["included_total"] = sum(d.get("included", 0) for d in days)
    a["considered_total"] = sum(d.get("considered", 0) for d in days)
    a["adopted_total"] = sum(d.get("adopted", 0) for d in days)
    if a["considered_total"]:
        a["adoption_rate_pct"] = round(100.0 * a["adopted_total"] / a["considered_total"], 1)
    a["title_core_ok_count"] = sum(1 for d in days if d["title_core_ok"])
    a["prefix_count"] = sum(1 for d in days if d["prefix_xnikki"])
    a["highlight_bracketed_count"] = sum(1 for d in days if d["highlight_bracketed"])
    a["highlight_contains_brackets_count"] = sum(1 for d in days if d["highlight_contains_brackets"])
    a["tags_always_4"] = all(d["tags_count"] == 4 for d in days)
    a["checks_match_all"] = all(d["checks_match"] for d in days)
    a["checks_url_passed_count"] = sum(1 for d in days if d["checks_url_check"] == "passed")
    a["checks_copy_passed_count"] = sum(1 for d in days if d["checks_copy_screen"] == "passed")
    a["checks_source_total"] = sum(d["checks_source_count"] for d in days)
    a["body_email_pattern_total"] = sum(d["body_email_pattern_count"] for d in days)
    a["cover_webp_disk_max"] = max(d["cover_webp_bytes_disk"] for d in days if d["cover_webp_bytes_disk"] is not None)
    a["cover_webp_disk_over_60000"] = [d["date"] for d in days if (d["cover_webp_bytes_disk"] or 0) > 60000]
    bt = [d["blog_total_bytes"] for d in days if "blog_total_bytes" in d]
    a["blog_days_measured"] = len(bt)
    a["blog_total_max"] = max(bt) if bt else None
    a["blog_total_min"] = min(bt) if bt else None
    a["blog_total_over_80000"] = [d["date"] for d in days if d.get("blog_total_bytes", 0) > 80000]
    a["blog_total_over_100000"] = [d["date"] for d in days if d.get("blog_total_bytes", 0) > 100000]
    a["blog_image_max"] = max(d["blog_image_bytes"] for d in days if "blog_image_bytes" in d)
    a["blog_image_over_60000"] = [d["date"] for d in days if d.get("blog_image_bytes", 0) > 60000]
    a["note_url_days"] = sum(1 for d in days if d["note_urls"])
    a["run_complete_count"] = sum(1 for d in days if d["run_complete_marker"])
    a["package_statuses"] = sorted(set(d["package_publication_status"] for d in days))
    a["body_bytes_min"] = min(d["body_bytes_disk"] for d in days)
    a["body_bytes_max"] = max(d["body_bytes_disk"] for d in days)
    a["body_disk_vs_reported_mismatch"] = [
        {"date": d["date"], "disk": d["body_bytes_disk"], "reported": d.get("body_bytes_reported")}
        for d in days if d.get("body_bytes_reported") is not None and d["body_bytes_reported"] != d["body_bytes_disk"]]
    a["blog_vs_reported_total_diff"] = [
        {"date": d["date"], "blog": d.get("blog_total_bytes"), "reported": d.get("day_total_reported")}
        for d in days if d.get("day_total_reported") is not None and d.get("blog_total_bytes") is not None and d["day_total_reported"] != d["blog_total_bytes"]]
    return a

days = {date: parse_day(date) for date in ALL}
out = {
    "population": "2026-11-06..2026-11-19 (14 days, Muse sole-handler period)",
    "days": [days[d] for d in ALL],
    "aggregates": {
        "old_2026-11-06_13": agg([days[d] for d in OLD]),
        "new_2026-11-14_19": agg([days[d] for d in NEW]),
        "all_14_days": agg([days[d] for d in ALL]),
    },
    "paper007_published_reference": {"received": 134, "considered": 81, "adopted": 63,
        "note": "Paper 007 findings per series ledger (served-image max 58,830; day-total max 71,968)"},
}
print(json.dumps(out, ensure_ascii=False, indent=1))

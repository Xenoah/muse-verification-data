#!/usr/bin/env python3
"""Paper 007 audit: x-note-collector diary pipeline, 2026-11-06..2026-11-13.
Read-only. Sources: local article packages (articles/<date>/) and per-day
run-state records (goals/x-note-collector/hidden_files/<date>-run-state.md).
"""
import json, os, re, sys

REPO = os.path.expanduser("~/workspace/x-note-collector-repo/x-note-collector-main")
STATES = os.path.expanduser("~/workspace/goals/x-note-collector/hidden_files")
DATES = [f"2026-11-{d:02d}" for d in range(6, 14)]

TITLE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (.+) ― 「(.+)」$")

def num(s):
    return int(s.replace(",", "")) if s else None

out = {"dates": [], "population": "2026-11-06..2026-11-13 (8 days, run-state records complete)"}
for date in DATES:
    d = {"date": date}
    pkg = os.path.join(REPO, "articles", date)
    aj = json.load(open(os.path.join(pkg, "article.json")))
    cj = json.load(open(os.path.join(pkg, "checks.json")))
    pj = json.load(open(os.path.join(pkg, "publication.json")))
    d["title"] = aj["title"]
    m = TITLE_RE.match(aj["title"])
    d["title_format_ok"] = bool(m) and m.group(1) == date
    d["tags_count"] = len(aj["tags"])
    d["source_urls_count"] = len(aj["source_urls"])
    d["checks_source_count"] = cj["source_count"]
    d["checks_source_url_check"] = cj["source_url_check"]
    d["checks_copy_screen"] = cj["source_copy_screen"]
    d["package_publication_status"] = pj["status"]
    d["body_bytes_disk"] = os.path.getsize(os.path.join(pkg, "body.md"))
    d["cover_webp_bytes_disk"] = os.path.getsize(os.path.join(pkg, "cover.webp"))

    txt = open(os.path.join(STATES, f"{date}-run-state.md")).read()
    d["runstate_chars"] = len(txt)
    # received / included
    m = re.search(r"posts_received (\d+), posts_included (\d+)", txt)
    if m:
        d["received"], d["included"] = int(m.group(1)), int(m.group(2))
    else:
        m = re.search(r"Received (\d+), (?:eligible|included) (\d+)", txt)
        if m:
            d["received"], d["included"] = int(m.group(1)), int(m.group(2))
    # considered / adopted
    m = re.search(r"(\d+) considered / (\d+) adopted", txt) or re.search(r"(\d+) adopted / (\d+) considered", txt)
    if m:
        if "adopted /" in txt[m.start()-0:m.end()+30] or txt[m.start():m.end()].split("/")[0].strip().split(" ")[-1].isdigit() and "adopted" in txt[max(0,m.start()-40):m.end()+10]:
            pass
        d["considered_adopted_raw"] = m.group(0)
    m2 = re.search(r"body\.md ([\d,]+) bytes; (\d+) considered / (\d+) adopted", txt)
    if m2:
        d["body_bytes_reported"] = num(m2.group(1)); d["considered"] = int(m2.group(2)); d["adopted"] = int(m2.group(3))
    m2 = re.search(r"body\.md ([\d,]+) bytes\. (\d+) adopted / (\d+) considered", txt)
    if m2:
        d["body_bytes_reported"] = num(m2.group(1)); d["adopted"] = int(m2.group(2)); d["considered"] = int(m2.group(3))
    m2 = re.search(r"body\.md ([\d,]+) bytes; (\d+) considered / (\d+) adopted", txt)
    if m2:
        d["body_bytes_reported"] = num(m2.group(1)); d["considered"] = int(m2.group(1+1)); d["adopted"] = int(m2.group(3))
    if "body_bytes_reported" not in d:
        m2 = re.search(r"body\.md ([\d,]+) bytes", txt)
        if m2: d["body_bytes_reported"] = num(m2.group(1))
    # served sizes / total
    m = re.search(r"image \(re-encoded[^)]*\) ([\d,]+) bytes, index\.html ([\d,]+) bytes, TOTAL ([\d,]+) bytes", txt)
    if m:
        d["served_image_bytes"], d["index_bytes"], d["day_total_bytes"] = num(m.group(1)), num(m.group(2)), num(m.group(3))
    else:
        m = re.search(r"Day total ([\d,]+) bytes \(image ([\d,]+) \+ index ([\d,]+)\)", txt)
        if m:
            d["day_total_bytes"], d["served_image_bytes"], d["index_bytes"] = num(m.group(1)), num(m.group(2)), num(m.group(3))
    # cover webp reported
    m = re.search(r"animated WebP ([\d,]+) bytes", txt)
    if m: d["cover_webp_bytes_reported"] = num(m.group(1))
    m = re.search(r"GIF ([\d,]+) bytes", txt)
    if m: d["cover_gif_bytes"] = num(m.group(1))
    # completion markers
    d["note_url_in_runstate"] = re.findall(r"https://note\.com/xenoah_memo/n/[a-z0-9]+", txt)
    d["record_publication_done"] = bool(re.search(r"record-publication \(DONE\)|record-publication run #\d+, ID \d+, success|record-publication.*Success", txt))
    d["link_note_done"] = bool(re.search(r"link-note \(DONE\)|link-note: public head|link-note.*Success|link-note generated", txt))
    d["persona_claim_in_runstate"] = "persona character" in txt
    d["ai_corner_mentioned"] = bool(re.search(r"AI-model corner (INCLUDED|OMITTED|NONE)|AI-model corner INCLUDED|AI-model corner: NONE", txt))
    m = re.search(r"AI-model corner (INCLUDED|OMITTED|NONE)", txt) or re.search(r"AI-model corner: (NONE)", txt)
    if m: d["ai_corner"] = m.group(1)
    out["dates"].append(d)

# aggregates
ds = out["dates"]
agg = {}
agg["days"] = len(ds)
agg["received_total"] = sum(d.get("received", 0) for d in ds)
agg["included_total"] = sum(d.get("included", 0) for d in ds)
agg["adopted_total_checks"] = sum(d["checks_source_count"] for d in ds)
agg["title_format_ok_count"] = sum(1 for d in ds if d["title_format_ok"])
agg["tags_always_4"] = all(d["tags_count"] == 4 for d in ds)
agg["source_count_matches_urls"] = all(d["checks_source_count"] == d["source_urls_count"] for d in ds)
agg["cover_webp_disk_max"] = max(d["cover_webp_bytes_disk"] for d in ds)
agg["cover_webp_disk_over_60000"] = [d["date"] for d in ds if d["cover_webp_bytes_disk"] > 60000]
tot = [d["day_total_bytes"] for d in ds if "day_total_bytes" in d]
agg["day_totals_known"] = len(tot)
agg["day_total_max"] = max(tot) if tot else None
agg["day_total_over_80000"] = [d["date"] for d in ds if d.get("day_total_bytes", 0) > 80000]
agg["served_image_over_60000"] = [d["date"] for d in ds if d.get("served_image_bytes", 0) > 60000]
agg["body_disk_vs_reported_mismatch"] = [
    {"date": d["date"], "disk": d["body_bytes_disk"], "reported": d.get("body_bytes_reported")}
    for d in ds if d.get("body_bytes_reported") is not None and d["body_bytes_reported"] != d["body_bytes_disk"]]
agg["package_publication_statuses"] = sorted(set(d["package_publication_status"] for d in ds))
agg["record_publication_done_count"] = sum(1 for d in ds if d["record_publication_done"])
agg["link_note_done_count"] = sum(1 for d in ds if d["link_note_done"])
agg["persona_claim_count"] = sum(1 for d in ds if d["persona_claim_in_runstate"])
out["aggregates"] = agg
print(json.dumps(out, ensure_ascii=False, indent=1))

#!/usr/bin/env python3
"""Paper 012 audit: full-population inventory of Muse's long-term memory.

Population: ~/MEMORY.md plus every file under ~/memory/.
Read-only. Records per-file bytes/lines (metadata and line counts only;
daily-log and bank contents are not reproduced), category breakdown,
daily-log continuity over the observed date range, people/groups INDEX
consistency (entries vs files on disk, both directions), and an
email-pattern COUNT over contents (matching strings are never output).
Usage: audit012.py <output.json>
"""
import json, os, re, sys, statistics
from collections import defaultdict
from datetime import datetime, timezone, timedelta, date

HOME = os.path.expanduser("~")
MEM_ROOT = os.path.join(HOME, "memory")
CURATED = os.path.join(HOME, "MEMORY.md")
JST = timezone(timedelta(hours=9))
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
DAILY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
INDEX_LINK_RE = re.compile(r"`~/memory/(people|groups)/([^`]+)`")

def file_stats(path):
    with open(path, "rb") as f:
        data = f.read()
    text = data.decode("utf-8", errors="replace")
    return {
        "bytes": len(data),
        "lines": text.count("\n") + (1 if text and not text.endswith("\n") else 0),
        "email_pattern_matches": len(EMAIL_RE.findall(text)),
    }

def category_of(rel):
    if rel == "MEMORY.md":
        return "curated"
    parts = rel.split(os.sep)
    if len(parts) == 2 and DAILY_RE.match(parts[1]):
        return "daily"
    if parts[1] == "bank":
        return "bank"
    if parts[1] == "people":
        return "people"
    if parts[1] == "groups":
        return "groups"
    if parts[1] == "shopping":
        return "shopping"
    return "other"

def parse_index(path, kind):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    return [m.group(2) for m in INDEX_LINK_RE.finditer(text) if m.group(1) == kind]

def main():
    out_path = sys.argv[1]
    started = datetime.now(JST)
    files = []  # (rel, category, stats)
    errors = []
    targets = [("MEMORY.md", CURATED)]
    for dirpath, dirnames, filenames in os.walk(MEM_ROOT):
        dirnames.sort()
        for name in sorted(filenames):
            p = os.path.join(dirpath, name)
            rel = os.path.join("memory", os.path.relpath(p, MEM_ROOT))
            targets.append((rel, p))
    for rel, p in targets:
        try:
            st = file_stats(p)
        except OSError as e:
            errors.append(f"{rel}: {e}"[:200])
            continue
        st["rel"] = rel
        st["category"] = category_of(rel)
        st["mtime"] = datetime.fromtimestamp(os.lstat(p).st_mtime, JST).isoformat()
        files.append(st)

    cats = defaultdict(lambda: {"files": 0, "bytes": 0, "lines": 0})
    for f in files:
        c = cats[f["category"]]
        c["files"] += 1
        c["bytes"] += f["bytes"]
        c["lines"] += f["lines"]

    # daily continuity
    daily = sorted((f for f in files if f["category"] == "daily"),
                   key=lambda f: f["rel"])
    daily_dates = []
    for f in daily:
        name = os.path.basename(f["rel"])[:-3]
        daily_dates.append(datetime.strptime(name, "%Y-%m-%d").date())
    expected = []
    d = daily_dates[0]
    while d <= daily_dates[-1]:
        expected.append(d)
        d += timedelta(days=1)
    missing = [str(x) for x in expected if x not in set(daily_dates)]
    daily_bytes = [f["bytes"] for f in daily]
    daily_lines = [f["lines"] for f in daily]
    daily_detail = [{"date": str(dt), "bytes": f["bytes"], "lines": f["lines"]}
                    for dt, f in zip(daily_dates, daily)]

    # index consistency
    consistency = {}
    for kind in ("people", "groups"):
        idx_rel = f"memory/{kind}/INDEX.md"
        idx_path = os.path.join(MEM_ROOT, kind, "INDEX.md")
        listed = parse_index(idx_path, kind)
        on_disk = sorted(os.path.basename(f["rel"]) for f in files
                         if f["category"] == kind
                         and os.path.basename(f["rel"]) != "INDEX.md")
        consistency[kind] = {
            "index_entries": len(listed),
            "listed_files": sorted(listed),
            "pages_on_disk": len(on_disk),
            "listed_but_missing_on_disk": sorted(set(listed) - set(on_disk)),
            "on_disk_but_not_listed": sorted(set(on_disk) - set(listed)),
        }

    total_bytes = sum(f["bytes"] for f in files)
    total_lines = sum(f["lines"] for f in files)
    largest = sorted(files, key=lambda f: -f["bytes"])[:10]
    results = {
        "measured_at": started.isoformat(),
        "population": "~/MEMORY.md + ~/memory/**",
        "total_files": len(files),
        "total_bytes": total_bytes,
        "total_lines": total_lines,
        "read_errors": errors,
        "categories": {k: cats[k] for k in
                       ["curated", "daily", "bank", "people", "groups",
                        "shopping", "other"] if k in cats},
        "daily": {
            "count": len(daily),
            "first": str(daily_dates[0]),
            "last": str(daily_dates[-1]),
            "expected_days_in_range": len(expected),
            "missing_dates": missing,
            "bytes_min": min(daily_bytes), "bytes_max": max(daily_bytes),
            "bytes_median": statistics.median(daily_bytes),
            "bytes_total": sum(daily_bytes),
            "lines_total": sum(daily_lines),
            "smallest": min(daily_detail, key=lambda x: x["bytes"]),
            "largest": max(daily_detail, key=lambda x: x["bytes"]),
            "detail": daily_detail,
        },
        "bank_files": [{"name": os.path.basename(f["rel"]),
                        "bytes": f["bytes"], "lines": f["lines"]}
                       for f in sorted((x for x in files if x["category"] == "bank"),
                                       key=lambda x: -x["bytes"])],
        "index_consistency": consistency,
        "largest_files": [{"rel": f["rel"], "bytes": f["bytes"],
                           "lines": f["lines"]} for f in largest],
        "email_pattern_matches_in_contents_total":
            sum(f["email_pattern_matches"] for f in files),
        "files_with_email_pattern":
            sum(1 for f in files if f["email_pattern_matches"] > 0),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: results[k] for k in
                      ["total_files", "total_bytes", "total_lines",
                       "email_pattern_matches_in_contents_total",
                       "files_with_email_pattern"]}, ensure_ascii=False))
    print("daily:", results["daily"]["count"], results["daily"]["first"],
          "->", results["daily"]["last"], "missing:", missing)
    print("consistency:", json.dumps(consistency, ensure_ascii=False))

if __name__ == "__main__":
    main()

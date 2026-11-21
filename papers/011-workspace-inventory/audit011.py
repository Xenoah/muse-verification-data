#!/usr/bin/env python3
"""Paper 011 audit: full-population inventory of ~/workspace.

Read-only walk. Collects file counts, byte sums (lstat, symlinks not
followed), per-top-level-entry breakdown, extension distribution, size
buckets, largest files, mtime-month distribution, goals/ breakdown, and
an email-pattern scan over relative paths. Writes JSON results.
Usage: audit011.py <output.json>
"""
import json, os, re, sys, shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

ROOT = os.path.expanduser("~/workspace")
JST = timezone(timedelta(hours=9))
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

def bucket(size):
    if size == 0: return "0B"
    if size < 4096: return "1B-4KB"
    if size < 65536: return "4KB-64KB"
    if size < 1048576: return "64KB-1MB"
    if size < 10485760: return "1MB-10MB"
    if size < 104857600: return "10MB-100MB"
    if size < 1073741824: return "100MB-1GB"
    return ">=1GB"

def main():
    out_path = sys.argv[1]
    started = datetime.now(JST)
    total_files = 0
    total_bytes = 0
    total_dirs = 0
    symlinks = 0
    errors = []
    email_path_hits = 0
    per_top = defaultdict(lambda: {"files": 0, "bytes": 0, "dirs": 0})
    ext_count = Counter()
    ext_bytes = Counter()
    buckets = Counter()
    bucket_bytes = Counter()
    largest = []  # (bytes, relpath)
    mtime_months = Counter()
    mtime_month_bytes = Counter()
    goals_break = defaultdict(lambda: {"files": 0, "bytes": 0})
    dot_files = 0
    dot_bytes = 0

    def onerr(e):
        errors.append(str(e)[:200])

    for dirpath, dirnames, filenames in os.walk(ROOT, onerror=onerr, followlinks=False):
        rel_dir = os.path.relpath(dirpath, ROOT)
        top = "(root)" if rel_dir == "." else rel_dir.split(os.sep)[0]
        total_dirs += 1
        per_top[top]["dirs"] += 1
        for name in filenames:
            fpath = os.path.join(dirpath, name)
            rel = os.path.relpath(fpath, ROOT)
            try:
                st = os.lstat(fpath)
            except OSError as e:
                errors.append(f"lstat {rel}: {e}"[:200])
                continue
            if os.path.islink(fpath):
                symlinks += 1
            size = st.st_size
            total_files += 1
            total_bytes += size
            per_top[top]["files"] += 1
            per_top[top]["bytes"] += size
            ext = os.path.splitext(name)[1].lower() or "(none)"
            ext_count[ext] += 1
            ext_bytes[ext] += size
            b = bucket(size)
            buckets[b] += 1
            bucket_bytes[b] += size
            largest.append((size, rel))
            month = datetime.fromtimestamp(st.st_mtime, JST).strftime("%Y-%m")
            mtime_months[month] += 1
            mtime_month_bytes[month] += size
            parts = rel.split(os.sep)
            if parts[0].startswith("."):
                dot_files += 1
                dot_bytes += size
            if len(parts) >= 2 and parts[0] == "goals":
                g = goals_break[parts[1]]
                g["files"] += 1
                g["bytes"] += size
            if EMAIL_RE.search(rel):
                email_path_hits += 1
    largest.sort(reverse=True)
    du = shutil.disk_usage(os.path.expanduser("~"))
    finished = datetime.now(JST)
    results = {
        "root": ROOT,
        "measured_at_start": started.isoformat(),
        "measured_at_finish": finished.isoformat(),
        "total_files": total_files,
        "total_bytes": total_bytes,
        "total_dirs_including_root": total_dirs,
        "symlinks": symlinks,
        "walk_errors": len(errors),
        "walk_error_samples": errors[:20],
        "email_pattern_in_relative_paths": email_path_hits,
        "per_top_level": sorted(
            ({"name": k, **v} for k, v in per_top.items()),
            key=lambda d: -d["bytes"]),
        "extensions_by_count_top20": ext_count.most_common(20),
        "extensions_by_bytes_top20": sorted(ext_bytes.items(), key=lambda kv: -kv[1])[:20],
        "distinct_extensions": len(ext_count),
        "size_buckets": {b: {"files": buckets[b], "bytes": bucket_bytes[b]} for b in
                         ["0B", "1B-4KB", "4KB-64KB", "64KB-1MB", "1MB-10MB",
                          "10MB-100MB", "100MB-1GB", ">=1GB"]},
        "largest_files_top20": [{"path": p, "bytes": s} for s, p in largest[:20]],
        "mtime_months": sorted(mtime_months.items()),
        "mtime_month_bytes": sorted(mtime_month_bytes.items()),
        "goals_breakdown": sorted(
            ({"goal": k, **v} for k, v in goals_break.items()),
            key=lambda d: -d["bytes"]),
        "dot_top_level_files": dot_files,
        "dot_top_level_bytes": dot_bytes,
        "disk_usage_home_fs": {"total": du.total, "used": du.used, "free": du.free},
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print(json.dumps({k: results[k] for k in
                      ["total_files", "total_bytes", "total_dirs_including_root",
                       "symlinks", "walk_errors", "email_pattern_in_relative_paths",
                       "distinct_extensions"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()

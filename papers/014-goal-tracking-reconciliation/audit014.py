#!/usr/bin/env python3
"""Paper 014: three-surface reconciliation inventory of Muse's goal / tracked-item system.
Surfaces: (A) filesystem workspaces ~/workspace/goals/<slug>/ (GOAL.md header parse + per-dir file/byte census),
(B) assistant tracking roster (tracking-snapshot.json, from tracking.list tool),
(C) user goals roster (usergoal-snapshot.json, from user_goal.list tool).
Join key: slug. Email-pattern scan is COUNT ONLY on GOAL.md files (strings never output).
Read-only except printing JSON to stdout.
"""
import os, re, json, statistics
from pathlib import Path
from collections import Counter

HOME = Path.home()
ROOT = HOME / "workspace/goals"
HERE = Path(__file__).parent
EMAIL_RE = re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ID_RE = re.compile(r"^Goal ID:\s*(\S+)", re.M)
SLUG_RE = re.compile(r"^Goal slug:\s*(\S+)", re.M)

def main():
    tracking = json.loads((HERE / "tracking-snapshot.json").read_text())
    usergoals = json.loads((HERE / "usergoal-snapshot.json").read_text())
    t_items = tracking["items"]; u_items = usergoals["items"]
    t_slugs = [i["slug"] for i in t_items]; u_slugs = [i["slug"] for i in u_items]

    errors = 0; email_matches = 0; email_files = 0
    fs = []
    for d in sorted([x for x in ROOT.iterdir() if x.is_dir()], key=lambda x: x.name):
        slug = d.name
        gm = d / "GOAL.md"
        has_gm = gm.exists()
        gm_bytes = gm_lines = 0; gm_id = gm_slug = None
        if has_gm:
            try:
                data = gm.read_bytes()
                gm_bytes = len(data)
                gm_lines = data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)
                text = data.decode("utf-8", errors="replace")
                m = ID_RE.search(text); gm_id = m.group(1) if m else None
                m2 = SLUG_RE.search(text); gm_slug = m2.group(1) if m2 else None
                em = EMAIL_RE.findall(data)
                if em: email_matches += len(em); email_files += 1
            except Exception:
                errors += 1
        nfiles = 0; tbytes = 0; sub_counts = Counter(); cron_defs = 0
        for dirpath, dirnames, filenames in os.walk(d):
            for fn in filenames:
                fp = Path(dirpath) / fn
                rel = fp.relative_to(d)
                sub_counts[rel.parts[0] if len(rel.parts) > 1 else "(top)"] += 1
                if rel.parts[0] == "crons" if len(rel.parts) > 1 else False:
                    cron_defs += 1
                try: sz = fp.stat().st_size
                except Exception: errors += 1; continue
                nfiles += 1; tbytes += sz
        fs.append({"slug": slug, "has_goal_md": has_gm, "goal_md_bytes": gm_bytes, "goal_md_lines": gm_lines,
                   "goal_md_id_present": gm_id is not None, "goal_md_slug": gm_slug,
                   "goal_md_slug_matches_dir": (gm_slug == slug) if gm_slug else False,
                   "total_files": nfiles, "total_bytes": tbytes,
                   "files_docs": sub_counts.get("files", 0), "hidden_files": sub_counts.get("hidden_files", 0),
                   "cron_defs": cron_defs, "subdirs": sorted(sub_counts.keys())})
    fs_slugs = [f["slug"] for f in fs]
    fs_set, t_set, u_set = set(fs_slugs), set(t_slugs), set(u_slugs)
    out = {
        "root": str(ROOT),
        "read_errors": errors,
        "filesystem": {"dirs": len(fs), "with_goal_md": sum(1 for f in fs if f["has_goal_md"]),
                       "goal_md_id_present": sum(1 for f in fs if f["goal_md_id_present"]),
                       "goal_md_slug_matches_dir": sum(1 for f in fs if f["goal_md_slug_matches_dir"]),
                       "goal_md_slug_mismatch": [f["slug"] for f in fs if f["has_goal_md"] and not f["goal_md_slug_matches_dir"]],
                       "total_files": sum(f["total_files"] for f in fs), "total_bytes": sum(f["total_bytes"] for f in fs),
                       "goal_md_bytes_total": sum(f["goal_md_bytes"] for f in fs),
                       "goal_md_bytes_median": statistics.median([f["goal_md_bytes"] for f in fs if f["has_goal_md"]]) if fs else None,
                       "goal_md_bytes_max": max(({"slug": f["slug"], "bytes": f["goal_md_bytes"]} for f in fs), key=lambda x: x["bytes"], default=None),
                       "goal_md_bytes_min": min(({"slug": f["slug"], "bytes": f["goal_md_bytes"]} for f in fs if f["has_goal_md"]), key=lambda x: x["bytes"], default=None),
                       "max_total": max(({"slug": f["slug"], "bytes": f["total_bytes"], "files": f["total_files"]} for f in fs), key=lambda x: x["bytes"], default=None),
                       "dirs_with_cron_defs": sum(1 for f in fs if f["cron_defs"] > 0), "cron_defs_total": sum(f["cron_defs"] for f in fs),
                       "dirs_with_docs": sum(1 for f in fs if f["files_docs"] > 0), "docs_total": sum(f["files_docs"] for f in fs),
                       "hidden_total": sum(f["hidden_files"] for f in fs),
                       "empty_dirs": [f["slug"] for f in fs if f["total_files"] <= 1]},
        "tracking": {"items": len(t_items), "active": sum(1 for i in t_items if i["status"] == "active"),
                     "completed": sum(1 for i in t_items if i["status"] == "completed"),
                     "attention": Counter(i["attention"] for i in t_items)},
        "usergoals": {"items": len(u_items), "active": sum(1 for i in u_items if i["status"] == "active"),
                      "categories": Counter(i.get("category") for i in u_items)},
        "reconciliation": {
            "fs_only": sorted(fs_set - t_set - u_set),
            "tracking_only_no_fs": sorted(t_set - fs_set),
            "usergoal_only_no_fs": sorted(u_set - fs_set),
            "tracking_and_fs": sorted(t_set & fs_set),
            "usergoal_and_fs": sorted(u_set & fs_set),
            "tracking_and_usergoal_overlap": sorted(t_set & u_set),
            "union": len(fs_set | t_set | u_set)},
        "email_pattern_count_only_goal_md": {"matches": email_matches, "files": email_files},
        "per_goal": fs,
    }
    print(json.dumps(out, ensure_ascii=False, indent=1, default=dict))

if __name__ == "__main__":
    main()

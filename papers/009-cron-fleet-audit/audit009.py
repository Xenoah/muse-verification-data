#!/usr/bin/env python3
"""Paper 009 audit: full-population census of Muse cron scheduler fleet.
Jobs data transcribed verbatim from cron.list(include_disabled=true) output
returned 2026-11-15 05:46 JST in this run. Runs data parsed from the raw
cron.runs(limit=100) tool output saved as cron-runs-raw.json.
"""
import json, collections, pathlib

BASE = pathlib.Path(__file__).parent

# (id, enabled, is_system, is_heartbeat, owner, schedule_key, has_title)
JOBS = [
 ("chimera-request-processor", True, False, False, "goal:chimera-songs-and-summoning-space", "interval@15m", True),
 ("deterministic-doctor", True, True, False, None, "interval@1h", False),
 ("duolingo-daily-missions", True, False, False, "goal:duolingo", "daily@08:46:00", True),
] + [(f"feed-pulse-{i:02d}", True, True, False, None, f"daily@{i:02d}:00:00", False) for i in range(24)] + [
 ("github-calendar-daily-log", True, False, False, "goal:github-activity-calendar-history", "daily@23:46:00", True),
 ("github-repo-articles-daily-sync", True, False, False, "goal:github-pr", "daily@09:46:00", False),
 ("gmail-github-auto-sort", True, False, False, "goal:github-mail-auto-sort", "interval@1h", True),
 ("heartbeat", True, False, True, None, "interval@30m", False),
 ("mini-pc-price-watch", True, False, False, "goal:home-pc-for-running-muse", "daily@09:46:00", True),
 ("muse-use-cases-report-20261106", False, False, False, "goal:muse-2", "runonce@2026-11-06T12:09:00", True),
 ("musio-env-keepalive", True, False, False, "goal:musio-vnc-environment-and-orchestra-library-download", "daily@10:46:00", True),
 ("profile-image", True, True, False, None, "interval@168h", False),
 ("repo-article-daily", True, False, False, "goal:github-pr", "daily@19:46:00", True),
 ("research-paper-prep-evening", True, False, False, "goal:goal", "daily@17:46:00", True),
 ("research-paper-prep-morning", True, False, False, "goal:goal", "daily@05:46:00", True),
 ("research-paper-publish-evening", True, False, False, "goal:goal", "daily@18:46:00", True),
 ("research-paper-publish-morning", True, False, False, "goal:goal", "daily@06:46:00", True),
 ("shizuku-duplex-watch", True, False, False, "goal:shizuku-duplex", "daily@12:46:00", True),
 ("x-activity-calendar-nightly", True, False, False, "goal:x-google", "daily@23:46:00", True),
 ("x-note-collector-daily", True, False, False, "goal:x-note-collector", "daily@19:55:00", True),
 ("xin-zhao-aimoderu-hourly-refresh", True, False, False, "goal:ai-space", "interval@1h", False),
]

def kind_of(sk):
    if sk.startswith("interval@"): return "interval"
    if sk.startswith("daily@"): return "daily"
    if sk.startswith("runonce@"): return "runonce"
    return "other"

res = {}
res["total_jobs"] = len(JOBS)
res["enabled"] = sum(1 for j in JOBS if j[1])
res["disabled"] = sum(1 for j in JOBS if not j[1])
res["system_jobs"] = sum(1 for j in JOBS if j[2])
res["heartbeat_jobs"] = sum(1 for j in JOBS if j[3])
res["goal_owned"] = sum(1 for j in JOBS if j[4] and j[4].startswith("goal:"))
res["no_owner"] = sum(1 for j in JOBS if not j[4])
res["distinct_goal_owners"] = len({j[4] for j in JOBS if j[4]})
res["by_kind"] = dict(collections.Counter(kind_of(j[5]) for j in JOBS))
res["titled"] = sum(1 for j in JOBS if j[6])
res["untitled"] = sum(1 for j in JOBS if not j[6])
res["untitled_nonsystem"] = [j[0] for j in JOBS if not j[6] and not j[2]]
res["disabled_jobs"] = [j[0] for j in JOBS if not j[1]]
# daily fire times (HH:MM) among non-system daily jobs
daily_times = collections.Counter()
for j in JOBS:
    if kind_of(j[5]) == "daily" and not j[2]:
        daily_times[j[5].split("@")[1][:5]] += 1
res["nonsystem_daily_times"] = dict(sorted(daily_times.items()))
res["jobs_at_46min"] = sum(1 for j in JOBS if not j[2] and kind_of(j[5])=="daily" and j[5].split("@")[1][3:5]=="46")

# runs
raw = json.loads((BASE/"cron-runs-raw.json").read_text())
# tool output file wraps the JSON payload; locate the runs object
def find_runs(o):
    if isinstance(o, dict):
        if "runs" in o: return o
        for v in o.values():
            r = find_runs(v)
            if r: return r
    return None
robj = find_runs(raw)
runs = robj["runs"]
res["runs_window"] = len(runs)
res["runs_truncated_flag"] = robj.get("history_may_be_truncated")
res["runs_by_status"] = dict(collections.Counter(r["status"] for r in runs))
res["runs_by_job_top"] = collections.Counter(r["job_id"] for r in runs).most_common(8)
res["runs_distinct_jobs"] = len({r["job_id"] for r in runs})
res["runs_with_error_text"] = sum(1 for r in runs if r.get("error_text"))
res["runs_time_span_local"] = [runs[-1]["scheduled_for_local"], runs[0]["scheduled_for_local"]]

(BASE/"audit-009-results.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
print(json.dumps(res, ensure_ascii=False, indent=2))

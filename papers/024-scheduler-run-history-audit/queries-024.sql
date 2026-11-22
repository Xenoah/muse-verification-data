-- Paper 024 evidence queries (Muse DB, read-only, run 2026-11-22 JST)
-- Cutoff for all queries: scheduled_for < '2026-11-22T08:46:00Z'::timestamptz (= 2026-11-22 17:46 JST, this run's start)

-- Q1 totals
SELECT count(*) AS total_runs, sum(CASE WHEN status::text='succeeded' THEN 1 ELSE 0 END) AS succeeded,
       sum(CASE WHEN status::text='failed' THEN 1 ELSE 0 END) AS failed, count(DISTINCT job_id) AS distinct_jobs
FROM scheduler.job_runs WHERE scheduled_for < '2026-11-22T08:46:00Z'::timestamptz;

-- Q2 status distribution
SELECT status::text AS run_status, count(*) AS n FROM scheduler.job_runs
WHERE scheduled_for < '2026-11-22T08:46:00Z'::timestamptz GROUP BY status ORDER BY n DESC;

-- Q3 per-job aggregates (47 rows; joined with jobs for is_heartbeat/enabled; duration columns shown to be dispatch stamps)
SELECT r.job_id, j.is_heartbeat, j.enabled, count(*) AS runs,
       sum(CASE WHEN r.status::text='succeeded' THEN 1 ELSE 0 END) AS succeeded,
       sum(CASE WHEN r.status::text='failed' THEN 1 ELSE 0 END) AS failed,
       sum(CASE WHEN r.attempt>1 THEN 1 ELSE 0 END) AS retried_runs,
       sum(CASE WHEN r.worker_execution_timed_out THEN 1 ELSE 0 END) AS timed_out,
       round(avg((r.finished_at_utc - r.started_at_utc)/1000.0)::numeric,1) AS avg_duration_sec,
       max((r.finished_at_utc - r.started_at_utc)/1000) AS max_duration_sec
FROM scheduler.job_runs r JOIN scheduler.jobs j ON j.job_id = r.job_id
WHERE r.scheduled_for < '2026-11-22T08:46:00Z'::timestamptz
  AND r.started_at_utc IS NOT NULL AND r.finished_at_utc IS NOT NULL
GROUP BY r.job_id, j.is_heartbeat, j.enabled ORDER BY runs DESC LIMIT 60;

-- Q4 trigger reasons (raw + grouped)
SELECT trigger_reason, count(*) AS n FROM scheduler.job_runs
WHERE scheduled_for < '2026-11-22T08:46:00Z'::timestamptz GROUP BY trigger_reason ORDER BY n DESC;
SELECT CASE WHEN trigger_reason='scheduled' THEN 'scheduled' WHEN trigger_reason='maintenance_coalesced' THEN 'maintenance_coalesced' ELSE 'manual_other' END AS trigger_kind, count(*) AS n
FROM scheduler.job_runs WHERE scheduled_for < '2026-11-22T08:46:00Z'::timestamptz GROUP BY trigger_kind ORDER BY n DESC;

-- Q5 failed runs detail (error text truncated to 160 chars, categories assigned by Muse from the head text)
SELECT job_id, to_char(timezone('Asia/Tokyo', scheduled_for), 'YYYY-MM-DD HH24:MI') AS scheduled_jst, attempt, left(coalesce(error_text,''), 160) AS error_head
FROM scheduler.job_runs WHERE scheduled_for < '2026-11-22T08:46:00Z'::timestamptz AND status::text='failed' ORDER BY scheduled_for;

-- Q6 per-day (JST)
SELECT to_char(timezone('Asia/Tokyo', scheduled_for), 'YYYY-MM-DD') AS day_jst, count(*) AS runs,
       sum(CASE WHEN status::text='failed' THEN 1 ELSE 0 END) AS failed
FROM scheduler.job_runs WHERE scheduled_for < '2026-11-22T08:46:00Z'::timestamptz GROUP BY day_jst ORDER BY day_jst;

-- Q7 jobs table totals
SELECT count(*) AS total_jobs, sum(CASE WHEN enabled THEN 1 ELSE 0 END) AS enabled_jobs, sum(CASE WHEN is_heartbeat THEN 1 ELSE 0 END) AS heartbeat_jobs FROM scheduler.jobs;

-- Q8 timing integrity
SELECT count(*) AS runs_total, sum(CASE WHEN started_at_utc IS NULL THEN 1 ELSE 0 END) AS never_started,
       sum(CASE WHEN finished_at_utc IS NULL THEN 1 ELSE 0 END) AS never_finished,
       sum(CASE WHEN finished_at_utc - started_at_utc > 60000 THEN 1 ELSE 0 END) AS duration_over_60s,
       sum(CASE WHEN finished_at_utc - started_at_utc = 0 THEN 1 ELSE 0 END) AS duration_zero,
       max(finished_at_utc - started_at_utc) AS max_duration_ms,
       round(avg(started_at_utc - scheduled_for_utc)/1000.0::numeric,1) AS avg_start_delay_sec,
       max(started_at_utc - scheduled_for_utc)/1000 AS max_start_delay_sec
FROM scheduler.job_runs WHERE scheduled_for < '2026-11-22T08:46:00Z'::timestamptz;

-- Q9 jobs with no runs in window
SELECT j.job_id, j.enabled, j.schedule_kind, j.schedule_expr FROM scheduler.jobs j
WHERE NOT EXISTS (SELECT 1 FROM scheduler.job_runs r WHERE r.job_id = j.job_id AND r.scheduled_for < '2026-11-22T08:46:00Z'::timestamptz)
ORDER BY j.job_id;

-- Q10 retries / timeouts
SELECT sum(CASE WHEN attempt>1 THEN 1 ELSE 0 END) AS runs_attempt_gt1, max(attempt) AS max_attempt,
       sum(CASE WHEN worker_execution_timed_out THEN 1 ELSE 0 END) AS timed_out_runs
FROM scheduler.job_runs WHERE scheduled_for < '2026-11-22T08:46:00Z'::timestamptz;

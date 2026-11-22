# Diagram check record — Paper 024 (2026-11-22)
Engine: gpt-image-1.5 via OpenAI API (make_diagrams.py). Files in ~/workspace/goals/goal/hidden_files/illustrations/2026-11-22-024/

## diagram1-strata.png (資料図1: 層別失敗率)
- Attempt 1: all labels/numbers correct (All 47 jobs 0.71% / High-frequency jobs (100+ runs) 0.40% / Other 42 jobs 2.24%, title exact) but bar lengths were near-equal and not proportional to values — judged misleading for a bar chart, regenerated.
- Attempt 2 (adopted): labels/numbers exact; bar lengths approximately proportional (0.40% shortest ≈ half of 0.71%; 2.24% longest ≈ 3x 0.71%, ≈5.6x 0.40%). Verified visually against audit-024-results.json strata values. PASS.

## diagram2-failures.png (資料図2: 失敗の集中)
- Attempt 1 (adopted): top '13 failures in total'; boxes 'AI model refresh (hourly): 6', 'AI paper explainer: 3', 'Repo article daily: 2', 'X diary collector: 2', side box 'Other 43 jobs: 0 failures'. All numbers match audit-024-results.json failures.by_job (xin-zhao-aimoderu-hourly-refresh 6, ai-paper-explainer 3, repo-article-daily 2, x-note-collector-daily 2; 47-4=43 other jobs with 0). PASS.

## fig1-daily-runs.png (own-data figure)
- Made with matplotlib from audit-024-results.json daily_jst only (make_fig1.py). Days 11-15..11-22, runs 67/255/255/256/257/268/268/199, failures labelled 1/1/2/3/1/1/2/2. PASS.

# Diagram check record — Paper 025 (2026-11-23)
Engine: gpt-image-1.5 via OpenAI API (audit-025/make_diagrams.py; diagram2 regenerated once via a single-bar prompt). Files in ~/workspace/goals/goal/hidden_files/illustrations/2026-11-23-025/

## diagram1-injection.png (資料図1: 設定と掲載の不一致)
- Attempt 1 (adopted): title 'Setting vs actual listing'; left 'Setting: include_in_prompt', 'true: 2 of 9', 'false: 7 of 9'; right 'Actually listed', 'Skills listed: 3 of 8', 'Listed despite false: 2'. All labels/numbers verified against audit-025-results.json (include_true 2, include_false 7, skills_in_injected 3, false-but-listed 2). PASS on first check and on a second look after an interval.

## diagram2-categories.png (資料図2: カテゴリ別件数)
- Attempt 1: labels/numbers correct (Writing 3, Creation 2, Personal planning 1, Media 1, Work and knowledge 1) but each row had two unexplained bars — judged misleading, regenerated.
- Attempt 2 (adopted): exactly one bar per row, lengths approximately proportional (3 longest, 2 about two-thirds, 1s about one-third). Labels/numbers exact against audit-025-results.json categories. PASS.

## fig1-extensions.png (own-data figure)
- Prepared in the prep run with matplotlib from audit-025-results.json only (figures-025/fig1-extensions.png). PASS (prep record).

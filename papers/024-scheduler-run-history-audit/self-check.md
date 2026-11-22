# Paper 024 self fact-check (2026-11-22, separate pass)
- Re-ran totals query in a separate pass: total had rolled 1826 (first query) -> 1825 (evidence snapshot, consistent across Q1-Q10 and per-day sums) -> 1824 (self-check pass). All movement is in succeeded count at the oldest edge; failed = 13 in every pass, per-job failure counts unchanged. Draft discloses this in Ch.3 and Ch.7 and adopts the 1825 evidence snapshot. PASS with disclosure.
- Derived values recalculated: 13/1825=0.71%, 1812/1825=99.29%, 672/1825=36.82%, 336/1825=18.41%, 1176/1825=64.44%, 1512/1825=82.85%, 6/1512=0.40%, 7/313=2.24%, 153/1825=8.38%, 658/1825=36.05%, 4/47=8.5%, ratios 2.24/0.40=5.6x and 2.24/0.71=3.2x — all match draft.
- Failure category counts from the 13 error heads: external site 4, worker unfinished 3, platform termination/inference 5, dispatch uncertain 1 = 13. Match.
- feed-pulse family total 153 = 14 + 6 + 19 jobs x 7, from per-job aggregates. Match.
- Research series jobs 4 x 7 runs, 0 failures — confirmed in per-job aggregates.
- Draft scan: email-pattern 0 matches; disclaimer block present; chapter headings all 第X章 form (8 chapters); 活用方法 chapter grounded only in this audit's numbers.
- No personal email address in draft or evidence. No ToS-gray automation details (job names and aggregate stats only).
Result: PASS (self-check). Proceeding to ChatGPT review.

# muse-verification-data

note の連載「論文メモ」（AI論文解説、xenoah_memo）と「自律リサーチ論文」（xenoah_memo）で行った検証の証跡を公開するリポジトリです。
各記事で報告した数値が、どのような条件で、どのように測られたかを、誰でも追えるように残します。

検証は AI エージェント Muse が実施しました。ここにあるのは論文の公式結果ではなく、小型モデルによる小規模な方向性チェック（ローカル実測）と、論文の表の検算（机上検証）の記録です。

## 検証のルール

- 判定基準はモデルの実行前に決めて `criteria.md` に記録する（結果を見てから基準を動かさない）
- 条件ごとに複数回の試行を行い、試行ごとの生データを省略せず残す
- 失敗した試行や、計測の設計ミスで無効になった実行も、消さずに `invalid` として残す
- 実行環境（モデル名・量子化、推論エンジン、パラメータ、試行回数）を記録に明記する
- 個人情報・認証情報は含めない（絶対パス等は正規化済み）

## フォルダ構成

`explainers/<日付>-<論文スラッグ>/` に、1論文分の証跡が入っています。

| ファイル | 内容 |
|---|---|
| criteria.md | 実行前に固定した判定基準・設計 |
| criteria-addendum*.md | 実行途中で見つけた設計上の問題と修正の記録 |
| measure*.py | 計測スクリプト（使った問題データはスクリプト内または結果JSON内に収録） |
| raw_outputs.json | モデルの生成全文（生データ） |
| results*.json | 採点結果・集計 |
| desk-check.md | 机上検証（論文の表の再計算・整合性チェック） |
| run*.log | 実行ログ |
| *_invalid* | 無効として破棄した実行の記録（透明性のため保持） |

## 収録済みの検証

| 日付 | 論文 | 対応する note 記事 |
|---|---|---|
| 2026-11-17 | Kojima et al. 2022, Zero-shot-CoT (arXiv:2205.11916) | https://note.com/xenoah_memo/n/n1bfc9377ae15 |
| 2026-11-18 | Yang et al. 2023, OPRO (arXiv:2309.03409) | https://note.com/xenoah_memo/n/n1b15f1d3e2c2 |
| 2026-11-19 | Madaan et al. 2023, Self-Refine (arXiv:2303.17651) | https://note.com/xenoah_memo/n/n274cb45d1163 |
| 2026-11-20 | Yao et al. 2023, Tree of Thoughts (arXiv:2305.10601) | https://note.com/xenoah_memo/n/ne8320e81f983 |
| 2026-11-21 | Zheng et al. 2023, Step-Back Prompting (arXiv:2310.06117) | https://note.com/xenoah_memo/n/n50fa7d5fdd9b |
| 2026-11-22 | Gao et al. 2022, PAL: Program-Aided Language Models (arXiv:2211.10435) | https://note.com/xenoah_memo/n/n0077ff923cb7 |
| 2026-11-23 | Wang et al. 2023, Plan-and-Solve Prompting (arXiv:2305.04091) | https://note.com/xenoah_memo/n/ncaf57e8faf11 |
| 2026-11-24 | Zhou et al. 2023, Least-to-Most Prompting (arXiv:2205.10625) | https://note.com/xenoah_memo/n/nc520f8816fbb |

新しい記事の検証は、公開に合わせて順次追加されます。

## 自律リサーチ論文の検証データ

`papers/<番号>-<スラッグ>/` に、自律リサーチ論文シリーズ（全数監査型の調査報告）の証跡が入っています。各論文の数値の出所である監査スクリプト、集計結果JSON、証跡メモを収録しています（記事本文と図は note 側で公開されているため含みません）。

| ファイル | 内容 |
|---|---|
| audit*.py | 監査・計測スクリプト |
| *-results.json / *-evidence.json / *-snapshot.json | 集計結果・証跡データ |
| *-evidence-notes.md | 証跡メモ（先行調査、根拠対応、判断記録） |
| rerun-output.* / first-run-results.json | 再実行・初回実行の記録 |
| logs/ | 実行ログ（002のベンチマーク等） |

| 番号 | 論文 | 対応する note 記事 |
|---|---|---|
| 001 | ai-model-space-audit | https://note.com/xenoah_memo/n/n398da6f01e93 |
| 002 | cpu-inference-benchmark | https://note.com/xenoah_memo/n/n69a6dd65bfe8 |
| 003 | space-reaudit | https://note.com/xenoah_memo/n/n57bef0b52fdb |
| 005 | personal-information-privacy | https://note.com/xenoah_memo/n/n266fdaeddd4c |
| 006 | tsubuyai-editorial-audit | https://note.com/xenoah_memo/n/ne7620b684142 |
| 007 | diary-pipeline-audit | https://note.com/xenoah_memo/n/ndf31d2d2eddd |
| 008 | series-self-audit | https://note.com/xenoah_memo/n/n70a32f676d10 |
| 009 | cron-fleet-audit | https://note.com/xenoah_memo/n/n76998131585a |
| 010 | repo-queue-audit | https://note.com/xenoah_memo/n/n50c3d98c7ee4 |
| 011 | workspace-inventory | https://note.com/xenoah_memo/n/n766da539b509 |
| 012 | memory-inventory | https://note.com/xenoah_memo/n/n36ba9287ea52 |
| 013 | skill-library-inventory | https://note.com/xenoah_memo/n/nffe68ffc04f8 |
| 014 | goal-tracking-reconciliation | https://note.com/xenoah_memo/n/n8cdfd1b0a18f |
| 015 | connector-library-inventory | https://note.com/xenoah_memo/n/naa0e86af5f04 |
| 016 | space-inventory | https://note.com/xenoah_memo/n/nb6c39a68eb4b |
| 017 | musio-v3-audit | https://note.com/xenoah_memo/n/ne0642501d52c |
| 018 | explainer-production-audit | https://note.com/xenoah_memo/n/nfb9a270298c0 |
| 019 | diary-pipeline-followup | https://note.com/xenoah_memo/n/n1413e13bc5d9 |
| 020 | repo-queue-followup | https://note.com/xenoah_memo/n/n6072c6079510 |
| 021 | homepage-catalog-audit | https://note.com/xenoah_memo/n/n4cc2da72d703 |
| 022 | verification-data-audit | https://note.com/xenoah_memo/n/nebcfcc7a47d7 |
| 023 | research-notes-inventory | https://note.com/xenoah_memo/n/n2d3d9e6ce67c |
| 024 | scheduler-run-history-audit | https://note.com/xenoah_memo/n/n6bad4e64519a |
| 025 | custom-extensions-audit | https://note.com/xenoah_memo/n/n2b70bc86c027 |

第004回は記事を取り下げ済みのため、証跡も収録していません。

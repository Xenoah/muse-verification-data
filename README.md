# muse-verification-data

note の連載「論文メモ」（AI論文解説、xenoah_memo）で行った検証の証跡を公開するリポジトリです。
各記事の「ガチ検証」で報告した数値が、どのような条件で、どのように測られたかを、誰でも追えるように残します。

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

新しい記事の検証は、公開に合わせて順次追加されます。

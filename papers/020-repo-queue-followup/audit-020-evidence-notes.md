# 論文020 証跡メモ

## 対象と取得
- 対象: Space「GitHubリポジトリ紹介記事」(slug: githubripozitorishao-jie-ji-shi) の listrepos 全件。
- 取得: 2026-11-20 17:46台（JST）の本回で invoke。同期状態は at=2026-11-20T00:51:26.886Z / state=ok / message「102件のリポジトリを同期しました」。
- 生データ: listrepos-raw.json（本フォルダ、記事本文を含むため保管時はメタデータのみの snapshot-020-metadata.json を使う）。
- 基準点: 第10回（2026-11-15公開）の生スナップショット（同期 2026-11-15T00:50:53Z、86件）を listrepos-010-baseline-raw.json として複写し、集合比較に使用。第10回の公表集計は audit-010/audit-010-results.json。

## 先行研究チェック（2026-11-20、本回検索）
- 日本語クエリ「GitHub リポジトリ 棚卸し キュー 進捗管理 全数調査」: リポジトリ追跡ツール（スプレッドシート連携等）やメトリクス表示ツールの一般例を確認。
- 英語クエリ「repository inventory audit backlog growth tracking longitudinal study」: バックログ計測（CHAOSS等）や機関リポジトリの長期追跡の一般論を確認。
- いずれも、個人の記事化キューの全数を2時点で集合比較し、流入の内訳（新規作成か、既存の範囲拡大か）まで分解した報告ではなかった。独自性は手法ではなく本キュー自身の追跡実データに限定する。

## 集計方法
- audit020.py が listrepos の明細を独自に再集計し、Spaceの集計値（counts）と突合（完全一致）。
- 第10回スナップショットと fullName で集合比較: 追加・削除・状態遷移を数えた。
- 追加分は repoCreatedAt が前回同期日（2026-11-15）以降か以前か、および isPrivate で分解。
- メールアドレス形式は正規表現の一致件数のみ数え、文字列は抽出していない（結果0件）。
- 完了日時は Space の articleUpdatedAt（下書き保存時刻）を JST に換算した日付で読んだ。note公開時刻そのものではない。

## 主要結果（audit-020-results.json に追跡可能）
- 総数102（done 6 / pending 96 / draft 0 / editing 0）。第10回は86（done 2 / pending 84）。
- 同期間隔5日で追加16・削除0。追加の内訳: 2026-11-15以降に作成された公開repo 4件（archive_music, vrcworld_winter-brick-house, webapp_otoware-generator, gakkiey_android-ime-instrument）と、それ以前に作成されていたプライベートrepo 12件（作成日 2026-02-07〜2026-11-12）。
- プライベートは 0→12件（全体の11.8%）。manual フラグは全102件 false で、12件も手動追加ではなく同期で入った形跡。
- 共通86件の遷移: done→done 2、pending→done 1（XNH_news-atlas）、pending→pending 83。
- 完了6件のうち3件（archive_music, muse-research-archive, webapp_otoware-generator）はこの5日間にキューへ入り、その間に完了した新規組。
- 残り96件を1日1件で処理すると、2026-11-21を1日目として96日目は2027-02-24。第10回の見通し（2027-02-07）から17日後退。
- pending のまま記事本文（869字）とタイトルを持ち、draftError に空repo理由の却下記録があるものが1件（vrcworld_winter-brick-house）。

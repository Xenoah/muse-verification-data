# 第21回 証跡メモ（2026-11-21）

対象: Xenoah.github.io 作品カタログ（data/projects.json）全108件の全数監査。
台帳: Space「論文シリーズ・ステータス」で第21回として登録済み（id 21）。リクエスト紐づき論文なし、未公開の未完了論文なし（第4回は取り下げ確定のため対象外）のため、手順1(c)により新規テーマとして着手。

## 先行研究チェック（2026-11-21、ブラウザ検索 日英2クエリ）
- 日本語「個人サイト 作品カタログ 全数棚卸し 監査 リンク整合性」: ポートフォリオ監査ツール（AITSQL、57項目の自動チェック）、コンテンツインベントリ手法（Seenabl）等が存在。
- 英語「personal website project catalog audit link inventory completeness study」: コンテンツインベントリ／監査の一般的手法（WSU のガイド、リンク棚卸しの解説、内部リンク監査のSOP等）が存在。
- 本カタログ（projects.json 108件）自体を、正本データ・生成物・参照先リポジトリ分解まで全数照合した報告は確認できず。独自性は手法ではなく本カタログ自身の全数実データに限定する。

## 証跡
- 正本: ~/workspace/xenoah-github-io/data/projects.json（作業ツリーで未変更、git diff 空）。リポジトリ HEAD ca3b6e98365d48a3c6d07cb5476b5fe70edc1c76。なお repo 内にはブログ関連の無関係な未コミット変更2件があったが監査対象ファイルには含まれない。
- 規則の出典: 同 repo の docs/ADDING_PROJECTS.md（category 許容値9種、pagesUrl null 時は sourceOnlyReason 必須、updated は確認できる場合のみ等）と AGENTS.md（正本は projects.json、生成物を直接編集しない）。
- 独自監査: audit021.py（本フォルダ）で全件集計 → audit-021-results.json。
- サイト自身のゲート（読み取り専用モード）: `node scripts/build-projects.js --check` 終了コード0（「Project catalog: 108 projects, generated files current.」）。`node scripts/check-site.js` 終了コード0（SEO検査54ページ正常、「Site checks passed: 108 projects, ...」）。
- 生成物突合: _includes/project_catalog.html の <article> 108件・タイトル108/108・sourceUrl 108/108、_includes/site_menu.html のタイトル108/108、_includes/featured_projects.html の featured タイトル4/4、sitemap.xml の pagesUrl 46/46。
- 図: figures-021/fig1-catalog.png（本監査の集計データのみから作成、make_fig.py）。

## 主要数値（audit-021-results.json に追跡可能）
- 総数108、id一意108、タイトル一意108、重複0。カテゴリ9種すべて使用（software21/tools17/music16/games15/community11/images10/data8/models6/learn4）、許容外0、id形式違反0。
- pagesUrl あり46（42.59%）、null 62。null 62件全件に sourceOnlyReason あり（必須規則への適合62/62）。理由は26種、最頻は組み込みファームウェア11件。
- カテゴリ別: software は21/21がソースのみ（公開サイト0）。公開あり最多は games11。
- sourceUrl は108/108あり、全件 https。pagesUrl・sourceUrl とも完全な重複URL 0。
- 参照先リポジトリは distinct 86種: 外部 repo 85種が各1件（85件）＋自サイト repo（Xenoah/Xenoah.github.io）配下の23件。85+23=108。
- pendingPagesUrl は4件で、「公開サイト準備中」理由の4件と完全一致。
- updated は17/108（範囲2026-08-20〜2026-11-18、未来日0）。featured 4件、thumbnailSlug 35件。
- 説明文は108/108あり、長さ中央値46字、最短6字（4件）、最長154字。
- projects.json 内のメールアドレス形式は0件。

## 未測定（限界に明記）
- pagesUrl 46件の外部到達性（実際に表示されるか）は未測定。本稿は記録の整合性の監査。
- GitHub側の公開 repo 総数の独立した全数列挙は未実施（参照先 distinct 86 は記録上の主張と一致するが、GitHub API での裏付けはしていない）。
- 説明文の内容の正確性（実物との一致）は未検証。有無と文字数のみ測定。

# 第6回 証跡メモ（audit-006）

テーマ: AI編集サイト「つぶやいテック」の自己編集規則への適合性監査
実施: 2026-11-13 夕方・準備回（公開はしない）
対象: GitHubリポジトリ Xenoah/tsubuyai-tech の main、commit 77c661c65610cf7f6ef95d38970287fc2abd6d87（2026-11-12）
- ローカルクローン ~/workspace/tsubuyai-tech-work の HEAD と `git ls-remote origin main` の一致を監査当日に確認。つまり監査対象は公開中の版と同一。
- 全数: content/posts 30件、content/features 3件、計33件。agents 7名分。

## 先行研究チェック（2026-11-13、browser.search、日英2クエリ）
- 「AI生成ニュースサイト 編集方針 適合性 監査 全数検証」「audit AI-generated news site compliance own editorial policy full population verification」
- 見つかったのは各媒体の編集方針ページや一般的なAIコンテンツ倫理ガイドのみで、特定のAI編集サイトが自サイトの全記事を自らの編集規則と機械的に全数照合した監査報告は、今回の調査範囲では確認できなかった。本稿の独自性はこの範囲に限定して主張する。

## 方法
1. 独自監査: Pythonスクリプト audit006.py（本フォルダ）で全33件のMarkdown（見出し行＋JSONメタ＋本文）を解析し、EDITORIAL.md／docs/POST-FORMAT.md／docs/FEATURE-FORMAT.md／agents/*.md から抽出した規則と照合。規則の実装上の定義は scripts/content.mjs を参照して解釈した（例: 72時間ルールの基準日は最新訂正日）。
2. 交差検証: サイト自身の公開ゲートを実行。`npm test` = 35テスト全合格、`npm run check`（build --check）= "Content OK: 7 characters, 30 posts, 3 features"。
3. 初回実行で1件（20261016-gpt-live-1-1-voices）のレビュー日時が公開から72時間超と機械的に検出されたが、同記事には2026-10-18の訂正記録があり、検証器の定義する基準日（最新訂正日）で再計算すると違反0件だった。初回の検出は基準日の取り違えであり、論文には修正後の値を採用し、この経緯を限界ではなく方法に記録する。

## 主要数値（audit-006-results.json に追跡可能）
- 一次資料を持つ記事: 33/33。出典総数39件（primary 38、independent 1）。記事あたり出典数: 1件が27記事、2件が6記事。
- evidenceScope は全33件が primary-statement。独立裏付けを主張する記事は0件で、独立出典が1件しかない実態と自己申告が一致。
- 出典ホストは10種のみ（blog.google、developers.openai.com、openai.com、www.anthropic.com、huggingface.co、www.jpl.nasa.gov、www.ihub-tansa.jaxa.jp、www.riken.jp、www.r-ccs.riken.jp、www.t.u-tokyo.ac.jp）。担当別許可ドメイン違反 0件。
- 本文文字数（Unicodeコードポイント、検証器と同じ数え方）: ポスト最小88・最大487・中央値327。300字超（折りたたみ表示対象）16/30。担当上限超過 0件。長文は1509／1556／2438字で全て800〜12,000の範囲内。
- 日付: sourceDateから公開までの日数 0.84〜24.92日。担当maxAgeDays（radar 7日、その他30日。検証器は+1日の境界許容）超過 0件。
- レビュー: 全33件で7項目チェックが全てtrue、rights は全件 original-summary-no-media、出典確認→レビューの時系列違反 0件。
- 重複: 記事ID重複 0、ポストの一次出典URL重複 0。見出し行とメタ見出しの不一致 0、ファイル名とIDの不一致 0、本文中のURL・見出し記号・コード等の混入 0。
- 長文の連携: 3件全て postId が実在し、同一担当・ポスト以降の公開・1ポスト1本を満たす。
- 構成の偏り: ポスト担当別 hikari（AI）12、radar 8、sui 4、den 3、sora 2、riku 1、chise（知財）0。長文があるポストは3/30。訂正記録のある記事は1/33（上記GPT-Live記事）。
- 2026-11-12移行分11件（AIモデル速報の移行ポスト）は全件一次資料を持ち、reviewer は全件「Muse / 当該編集セッション」。

## 限界（論文にも明記）
- 本監査はメタデータの自己整合と形式規則への適合を検証したもので、出典本文が記事の主張を実際に支えるか（claimsSupported の実質）は再検証していない。レビュー記録の真実性は記録として扱った。
- 対象は2026-11-12時点の commit に固定されたスナップショットであり、その後の更新は含まない。
- 規則の解釈はリポジトリ同梱の検証器（scripts/content.mjs）を権威とした。検証器自体の正しさは本稿の対象外（ただし npm test 35件は検証器の振る舞いを別途テストしている）。

## 公開前チェック
- 個人メールアドレス: 本文・図・証跡のいずれにも含めない（アドレス形式文字列なし）。
- 規約グレーな自動化の運用詳細: 記載なし。本稿は公開リポジトリの公開情報のみを対象とする。
- 著作権: 他者の文章・表・図は複写していない。数値と規則の要約は自文で、出典を明記。図1は本監査自身の集計データからのみ作成。

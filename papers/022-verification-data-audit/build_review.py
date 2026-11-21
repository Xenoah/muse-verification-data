import json, pathlib, sys
d=pathlib.Path(__file__).parent
paper=(d/"paper-022-verification-data-audit.md").read_text()
res=json.loads((d/"audit-022-results.json").read_text())
summary={k:v for k,v in res.items() if k!="files_detail"}
_supp=pathlib.Path(d/"audit-022-supplement.json")
if _supp.exists(): summary["supplement"]=_supp.read_text()
prompt=f"""あなたは査読者です。以下は修正済みの第2稿です。前回の指摘（最多ファイル数の誤記、根拠未提示の主張）への対応として、誤記を修正し、監査集計データに supplement（ドメイン分類・README照合・ファイル名一覧・invalidファイル一覧・重複パスの特定）を追加しました。再レビューしてください。

## レビュー依頼（2つ）
(1) ファクトチェック: 事実誤り・数値の不整合・根拠のない主張を、該当箇所の引用と理由付きで全て指摘してください。数値は下部に添付する「監査集計データ（JSON）」と突き合わせて検証してください。問題が無ければ「重大な事実誤りなし」と明言してください。
(2) 面白さチェック（厳格採点）: 10点満点で採点してください。9点以上は「その分野の読者が保存・共有したくなる水準」に限ります。構成が整っているだけの文章は6点止まりです。評価の中心は「刺さり」です: 想定読者を具体的に1人想定し、その人の興味・こだわりに直接刺さる具体要素（意外な数字、失敗談、再現手順、定説を覆す結果など）が冒頭と本文に実在するかを最重視し、誰にでも当てはまる無難な文章は刺さりなしとして低く評価してください。弱い点と改善案も挙げてください。最後に「公開可否」の判断も一言ください。

## 下書き全文
{paper}

## 監査集計データ（JSON）
{json.dumps(summary, ensure_ascii=False, indent=1)}
"""
body={"model":"gpt-5","reasoning_effort":"low","messages":[{"role":"user","content":prompt}]}
out=d/f"gpt-review-req{sys.argv[1]}.json"; out.write_text(json.dumps(body,ensure_ascii=False))
print(out)

import json, os
base = os.path.expanduser("~/workspace/goals/goal/hidden_files/audit-019")
draft = open(os.path.join(base, "paper-019-diary-pipeline-followup.md"), encoding="utf-8").read()
res = json.load(open(os.path.join(base, "audit-019-results.json")))
agg = json.dumps(res["aggregates"], ensure_ascii=False, indent=1)
prompt = (
"あなたは査読者です。これは第2ラウンドのレビューです。第1ラウンドであなたは「重大な事実誤りなし、面白さ8/10、公開可」とし、軽微な指摘を2点挙げました。著者はその2点を次のとおり修正しました: (1)要旨の「報告値より全日で38〜40バイト大きく」を「報告値の得られた12日全てで…大きく」に修正。(2)「公開直前の値であることが裏付けられた」を「公開直前の時点の値である可能性が強く示唆された」に弱めた。あわせて第6章に実測の再現手順（3手順）を具体化しました。+38バイト差の内訳の特定は未測定事項として第8章に明記済みのため追加していません。\n\n"
"## レビュー依頼（2つ）\n"
"(1) ファクトチェック: 修正後の全文について、事実誤り・数値の不整合・根拠のない主張が残っていないか、添付の監査集計データ（JSON）と突き合わせて最終確認してください。問題が無ければ「重大な事実誤りなし」と明言してください。\n"
"(2) 面白さチェック（厳格採点）: 第1ラウンドと同じ基準（9点以上は保存・共有したくなる水準に限定、構成だけ整った文章は6点止まり、「刺さり」を最重視）で再採点し、刺さる具体要素を特定してください。最後に「公開可」か「公開不可」かを明言してください。\n\n"
"## 修正後の下書き全文\n" + draft + "\n\n## 監査集計データ（JSON・集計値）\n" + agg
)
req = {"model": "gpt-5", "messages": [{"role": "user", "content": prompt}]}
out = os.path.join(base, "gpt-review-req2.json")
json.dump(req, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print("wrote", out, os.path.getsize(out))

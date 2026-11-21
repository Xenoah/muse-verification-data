import json, os
base = os.path.expanduser("~/workspace/goals/goal/hidden_files/audit-020")
draft = open(os.path.join(base, "paper-020-repo-queue-followup.md"), encoding="utf-8").read()
res = json.load(open(os.path.join(base, "audit-020-results.json")))
trim = {k: res[k] for k in ("counts_from_space","sync","total_parsed","status_counter","done_pct","pending_pct","remaining_days_at_1_per_day","projection_start","projection_finish","languages","language_distinct","desc_present","desc_missing","desc_present_pct","topics_any","topics_none","stars_total","forks_total","open_issues_total","archived","is_fork","is_private","manual","created_years","updated_min","updated_max","emails_in_queue_data","done_info")}
trim["vs_010"] = {k: res["vs_010"][k] for k in ("old_total","old_done","old_pending","old_remaining","old_projection_finish_reported","added_count","removed_count","added_private","added_created_on_or_after_2026-11-15","added_created_before_2026-11-15","transitions","new_done_among_common")}
trim["anomalies_summary"] = {"pending_with_article_body_count": len(res["anomalies"]["pending_with_article_body"]), "pending_with_body_chars": res["anomalies"]["pending_with_article_body"][0]["body_chars"] if res["anomalies"]["pending_with_article_body"] else None, "done_private_count": len(res["anomalies"]["done_private"])}
agg = json.dumps(trim, ensure_ascii=False, indent=1)
prompt = (
"あなたは査読者です。以下の日本語の監査報告の下書きをレビューしてください。\n\n"
"## レビュー依頼（2つ）\n"
"(1) ファクトチェック: 事実誤り・数値の不整合・根拠のない主張を、該当箇所の引用と理由付きで全て指摘してください。数値は下部に添付する「監査集計データ（JSON）」と突き合わせて検証してください。問題が無ければ「重大な事実誤りなし」と明言してください。\n"
"(2) 面白さチェック（厳格採点）: 10点満点で採点してください。9点以上は「その分野の読者が保存・共有したくなる水準」に限ります。構成が整っているだけの文章は6点止まりです。評価の中心は「刺さり」です: 想定読者を具体的に1人想定し、その人の興味・こだわりに直接刺さる具体要素（意外な数字、失敗談、再現手順、定説を覆す結果など）が冒頭と本文に実在するかを最重視してください。誰にでも当てはまる無難な文章は「刺さりなし」として低く評価してください。弱い点と改善案も挙げてください。最後に「公開可」か「公開不可」かを明言してください。\n\n"
"## 下書き全文\n" + draft + "\n\n## 監査集計データ（JSON）\n" + agg
)
req = {"model": "gpt-5", "messages": [{"role": "user", "content": prompt}]}
out = os.path.join(base, "gpt-review-req1.json")
json.dump(req, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print("wrote", out, os.path.getsize(out))

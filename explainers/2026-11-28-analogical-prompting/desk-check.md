# 机上検証 — Analogical Prompting (arXiv:2310.01714) 2026-11-28
出典: arXiv HTML v3 を 2026-11-28 に直接確認。Table 1-5, §6, §8。

## Table 1 算数
- GSM8K GPT-3.5-turbo: 0-shot 75.0 / 0-shot CoT 75.8 / 5-shot CoT 76.7 / Ours 77.8
  検算: Ours - 0-shot CoT = +2.0pp (相対+2.64%), Ours - 5-shot = +1.1pp。整合。
- GSM8K text-davinci-003: 14.8 / 50.3 / 54.0 / 61.0 (†脚注: 例題生成のデモ付き)
  検算: Ours - 0-shot CoT = +10.7pp (相対+21.27%)。本論文最大級の伸び。ただし脚注条件あり。
- GSM8K PaLM2: 60.8 / 78.2 / 80.7 / 81.7 → Ours-0shotCoT=+3.5pp
- MATH GPT-3.5: 33.0 / 33.9 / 34.9 / 37.3 → Ours-0shotCoT=+3.4pp (相対+10.03%), Ours-5shot=+2.4pp
- MATH PaLM2: 27.1 / 29.8 / 34.3 / 34.8 → Ours-5shot=+0.5pp と小さい。モデル依存性あり。

## Table 2 Codeforces
- GPT-3.5-turbo-16k Acc@1: 0-shot 8 / 0-shot CoT 9 / 3-shot 11 / Exemplarsのみ 13 / Knowledge+Exemplars 15
  検算: 15-8=+7pp (相対+87.5%)。本文「GPT-3.5 (15%) が GPT-4 の 0-shot (16%) に competitive」は 15 vs 16 で整合。
- GPT-4 Acc@1: 16 / 16 / 17 / 17 / 19 → Knowledge版が最良。
- 注意: Acc@10 では GPT-3.5 Knowledge版 29 は 0-shot CoT 27 を上回るが、Exemplarsのみ 25 は下回る。Acc@1 と Acc@10 で順序が一部異なる点は本文で誇張しない。

## Table 3 BIG-Bench (GPT-3.5)
- Word sorting: 0-shot 66.8 / 0-shot CoT 67.6 / 3-shot 68.4 / Ours 75.2 → +7.6pp vs 0-shot CoT
- Logical deduction: 30.0/35.2/36.4/41.6, Temporal: 40.4/44.8/58.0/57.6 (3-shotに -0.4pp で負け), Colored objects: 50.4/61.6/62.0/68.0, Formal fallacies: 53.6/55.6/55.6/58.8
  → 全勝ではない (Temporal sequences)。「competitive with manual 3-shot」という論文表現は正確。

## Table 5 例題数 K
- GSM8K: K1 76.1, K2 77.0, K3 77.5, K4 77.3, K5 77.8
- MATH: K1 34.8, K2 36.7, K3 37.3, K4 37.0, K5 37.1
  → §6.5「K>=3 で consistent, best は K=3 or 5」と整合。単調増加ではない。

## Table 4 スケール (GSM8K)
- curie: Ours 2 vs retrieved 3 (-1), davinci-001: 9 vs 11 (-2), davinci-002: 48 vs 47 (+1), davinci-003: 61 vs 57 (+4)
  → §6.3/6.4「小型では retrieval が勝ち、大型では自己生成が勝つ」と数値が一致。交差点は davinci-002 付近。

## §6.6 定性分析
- 正解50件中: 例題が関連+正しい 35件 (70%), 関連だが解が誤り 9件, 無関係 6件
- 不正解50件中: 例題が関連+正しいのに解けない 28件 (56%, 内訳: 汎化ギャップ12, 例題への過依存8, 計算ミス等8), 関連だが誤解 12件, 無関係 10件
  → 「例題が良くても解けるとは限らない」が失敗の最大要因。記事で明記する。

## §8 限界 (著者自身)
- 推論計算量が増える (出力トークン増)
- モデルが弱い/関連知識を学習していないと自己生成が失敗する。強いモデル向き
- プロンプト表現への感度

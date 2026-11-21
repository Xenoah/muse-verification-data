# 実測の事前判定基準（実行前に記録、2026-11-18 12:10 JST頃）
対象論文: Yang et al. 2023, Large Language Models as Optimizers (OPRO), arXiv:2309.03409
中心的主張: AI自身に探索させた指示文 "Take a deep breath and work on this problem step-by-step." が、人間設計の "Let's think step by step." を GSM8K で上回る（論文表1/表4、PaLM 2-L scorer: 80.2% vs 71.8%、+8.4ポイント）。また意味的に似た文の組み合わせ "Let's work together to solve this problem step by step." は 49.4% まで落ちる（第5.2.3節）— 文面への感度が極端に大きい。

検証の目的: 同一モデル・同一問題で3指示文の正答率の順序が論文と同方向かを確認する。厳密な再現ではない（モデルは Qwen2.5-1.5B-Instruct Q4_K_M、問題は自作10問、昨日のゼロショットCoT実測と同一問題セットを再利用し条件だけ変える）。

判定基準（事前に固定）:
- 成功（方向一致）: B（深呼吸文）の正答率が A（一歩ずつ文）以上で、かつ B が3条件中の最高。
- 弱い一致: B = A（差0）で並ぶ最高。
- 不一致: B < A。
- 感度チェック: C（組み合わせ文）が A より低ければ論文第5.2.3節の方向と一致、そうでなければ不一致として報告。
- 安定性: 貪欲生成（temp 0）のため決定的。代表3問を条件Bで各3回繰り返し、出力一致を確認（決定的計測の最低3回ルール）。
- 試行数: 条件あたり10問（最低5を満たす）。全試行の生データを保存し、都合の良い試行だけを拾わない。
- パラメータ感度: 条件Bについて温度0.7・シード43でも10問を実行し、温度による振れ幅を記録する。

条件（問題文の後に指示文を置き、最後に "The answer is <数値>" の行で締める指示を共通で付ける）:
- A: "Let's think step by step."
- B: "Take a deep breath and work on this problem step-by-step."
- C: "Let's work together to solve this problem step by step."
モデル/生成: Qwen2.5-1.5B-Instruct Q4_K_M, llama.cpp 0.9.0-dev (827466b), temp 0.0, seed 42, max 256 tokens, CPUのみ。
注意（事前認識）: 論文の scorer は PaLM 2-L（大規模）。本VMの1.5B級では指示文の差が出ない可能性が高い。その場合は「小規模では差が出ない」こと自体を結果として報告する。

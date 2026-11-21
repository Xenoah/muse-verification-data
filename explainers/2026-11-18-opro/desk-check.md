# 机上検証メモ（2026-11-18、OPRO arXiv:2309.03409 HTML v2 を一次資料として検算）
出典箇所はすべて論文 HTML 版（v2）の表・節。

## 表1/表4（GSM8K、scorer = PaLM 2-L、ゼロショット test）
- 空文 34.0 / "Let's solve the problem." 60.8 / "Let's think step by step." 71.8 / Zhou et al. 長文 58.8
- OPRO最良 "Take a deep breath and work on this problem step-by-step." 80.2
- 検算: 80.2-71.8 = +8.4ポイント（1.117倍）。80.2-34.0 = +46.2ポイント。
- 要旨の "up to 8% on GSM8K" は、検算では +8.4ポイントが最も近い対応（%とポイントの表記ゆれの範囲。本文・結論部は "up to 8%" / "over 50%" と書く）。

## 第5.2.3節（文面感度、GSM8K test、PaLM 2-L）
- "Let's think step by step." 71.8 / "Let's solve the problem together." 60.5（-11.3）/ 両者の意味的合成 "Let's work together to solve this problem step by step." 49.4（-22.4）
- 意味が近い文同士でも最大22.4ポイント差。検算一致。

## 表6（転移、GSM8Kで見つけた深呼吸文を他データセットへ）
- PaLM 2-L: MultiArith 95.3（think 85.7、+9.6）/ AQuA 54.3（think 44.9、+9.4）。検算一致。

## 表4の scorer 違い
- text-bison scorer では PaLM 2-L-IT が見つけた Q_begin 長文は 64.4 で、"Let's think step by step." の 64.4 と同点。text-bison での最良は text-bison 自身が最適化した Q_end 文 68.5（+4.1）。
- → 最良文は scorer（採点モデル）に依存する。深呼吸文の優位は PaLM 2-L scorer での結果。

## 表7（BBH 23課題、PaLM 2-L-IT optimizer、overall = train+test 合算）
- 結論部の "sometimes over 50%" の対応: word_sorting (PaLM) overall 54.4 vs think 4.0 = +50.4ポイント。検算で裏付けあり。
- 本文の主張確認: think より +5超は PaLM 19/23課題（82.6%）、text-bison 15/23（65.2%）。空文より +5超は PaLM 20/23、text-bison 15/23。本文記述と一致。
- 反例: tracking_shuffled_objects_seven_objects (PaLM) は ours overall 19.6 vs think 60.8 = -41.2ポイントと大幅悪化。本文は "almost all" と留保しており、表と矛盾はしないが、要旨だけ読むと見落とす大きな負け課題。
- 内部不整合の疑い: snarks (text-bison、empty 行) training 77.1 / test 84.6 / overall 73.1。overall は train と test の加重平均のはずで、両者の区間 [77.1, 84.6] の外（73.1）には来ない。誤記とみられる。本記事の数値には使わない。

## 最適化過程（図1・第5.2.1節）
- "Let's do the math!" は Step 6 で訓練精度 78.2。深呼吸文は Step 107 で 80.2。差は +2.0ポイントに過ぎず、早い段階でほぼ同等の文が見つかっていた。本文自身がこの点を明記。
- デフォルト 200 steps、各 step で 8 指示文生成、meta-prompt には上位20指示文＋訓練例3件。評価時 temperature 0（貪欲）、optimizer は temperature 1.0。
- GSM8K 訓練サブセットは訓練集合の 3.5% サンプルで近似評価。

## 著者の限界（第7章ほか）
- optimizer LLM が誤答ケースを有効活用できていない（誤答を入れても結果は同程度）。
- プロンプト最適化には訓練集合（少なくとも数十件）が必要で、過適合の懸念（付録: 訓練精度が test より 5-20% 高いことが多いと自己言及）。
- 初期化への感度と探索/活用バランスが未解決課題。

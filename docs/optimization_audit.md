# two-seeds-logit 方案审计与下一步实验计划

> 对象：`references/biohub-cell-tracking-two-seeds-logit-blend.ipynb`（Public LB 0.912）
> 依据：**代码实际执行路径**（notebook 13 cell + runtime-patch 注入的 `repo/scripts/predict_unet_transformer.py`
> + `repo/src/biohub_tracking/{io,metrics,models}`）。Markdown 描述与代码冲突处均以代码为准。
> **【需日志验证】** = 无法从静态代码确定、需一次实际运行日志才能判定。

---

## 0. 一句话结论

这套方案真正决定最终连接拓扑的**不是 ILP，而是后处理里的 `motion_relink`**：它把 ILP + transformer
选出的边**整体丢弃**，用"运动 + 速度预测"的 Hungarian 重连，learned edge 证据只作为一个 **≤1.0µm 的 bonus**
参与。因此 0.912 之后的主战场在**关联侧"learned 证据的利用率"与验证/校准**，不在检测骨干、不在 ILP 权重、不在 division。

---

## 1. 实际执行流程（体数据 → submission.csv）

```
zarr (T,Z,Y,X)=(100,64,256,256)
  │ open_dataset(normalize=False, downsample=(1,4,4)) → 64³ 近各向同性
  │ 分位数归一化 q_low=attrs["0.001"], q_high=attrs["0.999"]        [predict:319-369]
  ▼
Primary UNet.encode → det_logits + unet_out
  │ ★检测 TTA：Cell9 patch 把 4-view 改 8-view D4(flip×3 + rot90 k=1,3 + transpose + anti-transpose)/8
  │           依赖 Y==X=64 成立
  ▼
Secondary UNet.encode → 同 8-view TTA
  │ ★检测融合(Cell9 patch#2)：逐帧全局 mean/std 对齐 secondary→primary
  │   det = 0.525*primary + 0.475*secondary_aligned      [scale_ratio clamp(0.5,2)]
  ▼
共享点提取：max_pool3d 局部极大 & sigmoid(det)>0.96875     [predict:285]  → 一套共享候选点
  ▼
predict_edges → edge_logits(n_src,n_tgt)
  │ ★边融合(Cell9 patch#3, low_margin_consensus)：primary_probs=softmax(dim0=父维)，top-2 margin/target；
  │   仅当 same_parent 且 primary margin 低 → blend_weight=0.15*uncertainty，否则 0
  │ raw=blended → probs=softmax(dim0) → 候选 E0={probs>0.48}    [predict:455-465]
  ▼
build_graph → ILPSolver(edge=-1.0*edge_prob, appear=0.0, disappear=1.5, div=1.0).solve()
  │ → 选中的边(含 ILP division)写入 .geff                     [predict:555-564]
  ▼ ═══ 以上在子进程；双 GPU 各跑一半 video 再 merge ═══
  ▼
读回 .geff → filter_output_graph()  [Cell11]，顺序：
  1. 丢非相邻帧 / >14µm 边
  2. ★motion_relink：全相邻帧 Hungarian(tight6→relaxed10µm)，
     cost = motion_dist + 0.05*raw − 1.0*learned_prob，
     **整体替换 edges = motion_edges**（严格 1:1，无 division）    [Cell11:2655-2658, 2770]
  3. single-parent repair（此时已 1:1，近 no-op）；single-child repair=OFF
  4. close_single_frame_gaps（effective_gap=min(2,1)=1；DeepCenter 仅确认 span≥8.5µm 的 synthetic 中点）
  5. recover_strict_gap2 = OFF
  6. add_safe_divisions_postlink：**唯一的 division 来源**（几何门 + 极小 cap）
  7. division_geometry_filter=OFF；prune_isolated；filter_short_track(<6 且非 division 删)；linefit_smooth
  ▼
写 node/edge 行 → submission.csv；run_stats.csv（诊断计数，始终写）
```

**核心事实**：ILP 输出不是最终连接。第 2 步 motion_relink 拍平并重连，ILP 主要贡献退化为
①提供 `edge_prob` bonus 集合、②大帧回退兜底。

---

## 2. 审计结果表

| 严重度 | 代码位置 | 问题 | 确定性 | 潜在影响 | 修复 |
|---|---|---|---|---|---|
| 高 | Cell11:2655-2658 | `motion_relink` 运动 Hungarian **整体替换** ILP/transformer 边；学习证据仅 `−1.0*prob` bonus（对比运动 cost 数 µm 偏弱） | 确定 | dual-seed edge blend + ILP 边级贡献被大幅稀释；最终拓扑由运动决定 | 见实验1 |
| 高 | Cell11:2696 + 2655 | motion_relink 拍平成 1:1 → **ILP division 结构被丢弃**；最终 division 仅来自 `add_safe_divisions_postlink`（几何、cap≈0.375%）。→ **ILP_DIVISION_WEIGHT / APPEARANCE 几乎不到输出** | 确定 | ILP 三权重里只有 disappear=1.5 间接影响 bonus 集合 | 勿调 ILP div 权重追 division |
| ~~高~~→无 | io.save_graph→`to_geff`(predict:564) → 读回 Cell11:2791 | ILP solution GraphView 经 `to_geff` 后 edge_prob 是否保留 | ✅**已验证(v8 exp2)：100% 穿透** (743034/743034 non-null) → edge blend 真接上，**无缺陷** | 无（原担心的"边级学习白跑"被证伪） | — |
| 中 | Cell11:1911 | `effective_gap_max=min(GAP_CLOSE_MAX_GAP,1)`；env=2 但**恒钳到 1** | 确定 | `GAP_CLOSE_MAX_GAP=2` 无效 | 死参 |
| 中 | Cell4:120 + Cell5:182 | `RUN_OUTPUT_DIAGNOSTICS` 定义后**全程未引用** | 确定 | 设 0/1 都不改 submission | 死变量 |
| 中 | Cell9 predict_cmd 无 `--evaluate`；metrics.summarise 存在 | 自带**竞赛同款本地打分器**但从不调用 | 确定 | 当前**零本地指标**，实验无客观信号 | 见实验0 |
| 低 | Cell7:913 | `secondary_mix_temperature=1.0` → `if !=1.0` 分支跳过 | 确定 | 温度当前 no-op | 无需处理 |
| 低 | Cell5:248 注释 vs Cell4:112-118 | 注释 "keeps it disabled" 过时；本次实际启用 DeepCenter 且 REQUIRE=1 | 确定 | 仅文档误导 | 以代码为准 |
| 低 | Cell9 patch 顺序/断言 | patch 精确整块匹配 + `count==1` + `compile()`；块没命中 hard-fail，**无静默单模型回退** | 确定(良性) | 上游脚本一改即崩（维护脆点） | 升级 pack 需重对齐字符串 |
| 低 | Cell9 merge/checksum | 双 GPU 分片 disjoint + 重复检测 + 覆盖 assert；primary/secondary sha256 校验 + DeepCenter epoch 锁 500 | 确定(良性) | 确定性/合并安全 | 保持 |

**分类小结**
- **确定存在**：motion_relink 覆盖学习边（高杠杆）、ILP division/appearance 近失效、GAP_CLOSE_MAX_GAP=2 死参、RUN_OUTPUT_DIAGNOSTICS 死变量、无本地打分。
- **可能存在**：edge_prob 是否穿过 ILP（决定 edge blend 是否有效）——**必须先验证**。
- **确认无问题**：8-view TTA patch 正确（依赖 Y==X 成立）；softmax(dim=0) 语义正确；双 GPU 合并/校验健壮；无静默降级。
- **实际未生效参数**：`GAP_CLOSE_MAX_GAP`(2→1)、`RUN_OUTPUT_DIAGNOSTICS`、`secondary_mix_temperature`(=1)、`ILP_APPEARANCE_WEIGHT`/`ILP_DIVISION_WEIGHT`、`recover_strict_gap2`/`gap2_*`(OFF)、`ADAPTIVE_SHORT_TRACK_RESCUE`/`short_track_rescue_*`(OFF)、`OUTPUT_DIVISION_GEOMETRY_FILTER`/`DIV_*`(OFF)、`OUTPUT_SINGLE_CHILD_REPAIR`(OFF)。

**点名审计小问的结论**
- **softmax 维度(Q8/Q9)**：`softmax(raw,dim=0)`，dim0=源=父维（predict:456）。对每个 target(子) 在候选 parents 上归一 → 允许 division、抑制 merge，与训练一致，**正确**。low_margin_consensus 的 top-2 margin / same_parent 也在父维/每 target，**维度自洽**。
- **检测 mean/std 对齐(Q7)**：逐帧全局对齐到 primary 的 mean/scale → 融合场≈保留 primary 绝对标定，det 阈值 0.96875 语义**未被破坏**；副作用见 §3-①。
- **ILP 输入(Q10)**：`edge_weight=-1.0*EdgeAttr("edge_prob")`，edge_prob = blend 后 logit 的 **softmax 概率∈[0,1]**（非 sigmoid、非 raw）。符号一致。但穿透性见上表。
- **runtime patch 脆弱性(Q11)**：精确整块 + `count==1` + `compile()` 校验，上游一改即 hard-fail（不静默）——确定性优点，但维护脆点。

---

## 3. 剩余误差 Top-5（含证据 / 置信度 / 验证 / 理论收益）

**① 稠密区身份交换 — 置信度 高，理论收益最大**
证据：拓扑由 motion_relink（motion+0.05raw−1.0prob）决定，learned 证据被压到 ≤1µm bonus（Cell11:2770）。
需验证：held-out 上 motion_relink 前/后 edge_jaccard 与 swap 计数；`motion_relink_fallback_raw` 触发频率。
收益：中（learned 管线唯一能进一步兑现处）。

**② 边级学习证据可能没进输出 — ✅已验证否决（v8 exp2）**
结论：geff edge_prob **100% 非空**（743034/743034）→ dual-seed edge blend + low_margin_consensus 完整进入
raw ILP 图与 motion_relink 的 learned bonus。**不是缺陷**，无需回填修复。→ 剩余收益转移到 ①（bonus 兑现）。

**③ 共享检测把单模型正确峰压到阈值下 — 置信度 中**
证据：near-balanced 0.475 + det 阈值极高 0.96875 → 仅在一个模型里高的峰，融合后≈0.525×峰高易跌破阈值。
需验证：node_recall@7µm，按 detection weight∈{0,0.475,1} 三点对比。

**④ min_track_len=6 删除真实短轨迹 — 置信度 中，收益小低风险**
证据：Cell11:2407，100 帧里 <6 节点非-division 分量被删；`short_track_nodes_removed` 有计数但无 GT-match 对照。
需验证：被删节点里 GT-matched 比例。

**⑤ 验证/校准缺失（横切）— 置信度 高**
证据：无本地打分、无按 embryo/密度分组、无阈值-召回曲线 → 所有参数对 Public LB 盲调。
收益：不直接加分，但是其余实验的前提。

（检测 localization / gap repair / division 因权重或占比小已近饱和，判低收益，见 §6。）

---

## 4. 模块贡献消融表（单变量；held-out train + metrics.summarise）

| # | 关闭/改动 | 冻结 | 记录指标 | 交互 |
|---|---|---|---|---|
|1|Primary only(secondary=0)|阈值/TTA/后处理|node_recall, edge_jaccard|与③耦合|
|2|+8-view TTA(对比4-view)|其余|node_recall, localization|与阈值耦合|
|3|+Secondary detection blend(0/0.475)|edge 冻结|node_recall@7µm|峰压制↔一致性|
|4|+Secondary edge blend(0/0.15)|检测冻结|candidate edge recall, edge_jaccard|**受②支配**|
|5|完整 dual-seed|—|全指标+按embryo|—|
|6|ILP on/off|motion_relink 保持 on|**motion_relink 前** edge_jaccard；fallback 频率|被 motion_relink 掩盖|
|7|motion_relink on/off|其余|edge_jaccard 前后差、swap 数|决定性模块|
|8|1-frame gap close on/off|—|gap acceptance precision|与 DeepCenter 耦合|
|9|DeepCenter gate on/off|gap 冻结|deepcenter_gap_accepted/rejected + edge_jaccard 变化|仅覆盖 span≥8.5µm synthetic 子集|
|10|short-track filter(6/off)|—|matched nodes/edges removed|与 motion 碎片化耦合|
|11|safe divisions on/off|—|division_jaccard TP/FP/FN|0.1 权重，天花板极低|
|12|linefit smooth(0.8/0)|—|localization err, edge_jaccard|弯曲/分裂附近可能负作用|

**提交门槛**：held-out（跨两 specimen，≥40 视频）上 adj_edge_jaccard 稳定 ≥ +0.002 且不伤任一 embryo 组，才提交。本地涨、单 embryo 掉 → 判过拟合，不提交。

---

## 5. 下一步实验（按 泛化收益 ÷ 成本 ÷ 风险 排序）

> **实验做法便利点**：把 `predictions/**/*.geff` 缓存下来，实验1/2/3 都**只需重跑 Cell 11**（后处理），
> 不必重跑 UNet 推理 → 秒级迭代。

### 实验0（必做前置）：接上本地打分 —— ✅**已跑完**（`src/v8_two_seeds_local_eval.ipynb`，见 §8）
- 目的：notebook 当前零本地指标，所有后续实验无判据。**已达成**：40 视频 held-out train 出 Score A/B/Δ/per-embryo。
- **已落地**：v8 = two-seeds 方案副本 + eval 层（gitignore 本地保留，因内嵌 pilkwang pack 源）。直接对
  **最终后处理图**（非 raw geff）用 pack 自带竞赛同款 metric 打分，并给出 raw-vs-final 分解。
- **改动位置**（相对 two-seeds notebook）：
  - Cell 4 追加 `BIOHUB_V8_EVAL/_N/_SEED` 控制块（默认 eval=1, N=40, seed=0）。
  - Cell 9 把 `test_stems = list_test_stems()` 换成 eval 分支：取 train 目录、按 specimen 分层抽 N 视频、`TEST_DIR←train`。
  - 末尾新增 scoring cell：逐视频 `evaluate(pred, GT.tracks, scale)` → **Score A**(raw ILP) / **Score B**(最终 pipeline)
    / **Δ=B−A**(后处理净贡献) / **按 embryo 分组** / **edge_prob 穿透 ILP 非空比例**（顺带做掉实验2 验证）。
    写 `v8_local_scores.csv`(逐视频×{raw,final})。
- **Kaggle 运行**：附 竞赛数据(含 train) + 与 two-seeds 相同 pack/权重/wheels 输入，GPU+internet ON，Run All。
  想快先设 `BIOHUB_V8_EVAL_N=20`；退回真实提交设 `BIOHUB_V8_EVAL=0`。
- **读数顺序**：先看 edge_prob 非空比例（≈0 → 实验2 命中）→ 再看 Δ(B−A) → 两 specimen 的 adj 一起看（泛化护栏）。
- **⚠️ train 泄漏**：primary/secondary 在 199 train 上训过、pack val 划分未知 → 绝对分偏乐观；只用**实验间 Δ** + 按 embryo 一致性决策。
- 成本≈一次 N 视频推理（N=40 ≈ 4-视频 test 的 ~10×，双 GPU 减半）；风险 0。

### 实验1（首选）：`MOTION_RELINK_LEARNED_BONUS` sweep —— ✅**已跑（1.0/1.5/2.0），结果见 §8**：方向证实（adj 单调↑、两 specimen 不降、收益集中稠密 44b6），但 b=1→2 adj 仅 +0.0014 且被 division 抵消 → **score 持平，不单独提交**。下一步扩 sweep（`1.0,2.0,3.0,4.0,6.0`）/ 实验1b override 逻辑。
- 假设：learned edge 证据是解稠密身份交换的唯一信息源，但 bonus(1.0) 相对运动 cost(数 µm) 太弱被埋没。
  **exp0 已强化此假设**：raw ILP（= bonus→∞ 完全让位 learned 边的极限）adj 0.9255 > final 0.9148，
  差 −0.011 全在后处理，且**稠密 44b6 −0.028 ≫ 稀疏 6bba −0.004** → motion_relink 覆盖 learned 边即漏分点。
- 证据：Cell11:2770 `cost = motion + 0.05*raw − BONUS*prob`；BONUS 默认 0.75，Cell4 设 1.0（基线）。
- 唯一变量：`BIOHUB_V8_BONUS_SWEEP`（初跑 `1.0,1.5,2.0`；默认已扩到 `"1.0,2.0,3.0,4.0,6.0"`）→ 打分 cell 自动逐 bonus 重跑后处理。
- 冻结：检测/边融合权重、阈值、gap、division、min_track_len 全不动（geff 缓存，只重跑 filter_output_graph）。
- 前置：~~实验2~~ 已完成（edge_prob 100% 穿透）→ 本实验有意义，可直接跑。
- 记录：per-bonus adj/edge_J、Δraw、**按 embryo**（notebook 末尾已打印 sweep 汇总表 + `v8_local_scores.csv` 带 `bonus` 列）。
- 成功判据：adj **随 bonus 单调↑并逼近 raw 的 0.9255**，且两 specimen 都不降 → 坐实漏分点 → 选最高档提交 LB。
  失败：adj 平/降 → learned 证据对拓扑无正贡献（motion 先验已足够）→ 锁回 1.0，edge blend 价值有限。
- 运行时间≈0（只重跑后处理，×3 bonus）；LB 过拟合风险 低（单调可解释）；值得提交：是（本地过关后）。

### 实验2（纠错/验证）：edge_prob 是否穿过 ILP —— ✅**已完成，结论：无缺陷**
- 结果（v8 exp0 打分 cell 顺带做掉）：geff edge_prob **non-null 743034/743034 = 1.000**。
- 结论：edge blend 完整进入输出，**不是缺陷**，无需回填修复 → 全部剩余收益压到实验1（bonus 兑现）。

### 实验3（次选，低风险精度/召回微调）：`OUTPUT_MIN_TRACK_LEN` 6→5
- 假设：6 在 100 帧偏严，删真实短轨迹；本 metric 不罚多余检测，放宽短轨迹多为净召回。
- 唯一变量：`BIOHUB_OUTPUT_MIN_TRACK_LEN` ∈ **{6(基线), 5}**（只降一级，勿到 4）。
- 记录：被删/保留分量的 GT-matched 比例、edge_jaccard、**adj**（注意 T_pred↑的密度惩罚）、按 embryo。
- 成功：adj ≥ +0.001 且两 specimen 均不降。失败：FP/密度惩罚 > 召回收益，锁回 6。
- 运行时间≈0；风险 低-中（须看 adj 而非裸 jaccard）。

> 不列入前三：dual-seed **detection** 权重(0.475) sweep —— 同时动召回与密度惩罚、LB 过拟合风险高；
> 先用实验0 的 node_recall 曲线确认是否瓶颈再决定。**禁止一次实验同时动检测+关联+后处理。**

---

## 6. 暂时不要尝试

- 换主检测/tracking 架构（SwinUNETR/Trackastra/ConvLSTM）—— 已到公开范式上限，瓶颈在后处理编排不在骨干。
- 调 ILP appearance/division 权重追 division —— 被 motion_relink 拍平触不到输出；division 仅 0.1 权重、占比 0.117%，天花板 <0.001。
- 降 det 阈值 / 高召回检测 —— 与融合+密度惩罚强耦合，等于一次动多隐变量；历史已证高召回检测 LB-negative。
- linefit / gap / DeepCenter 参数魔改 —— 覆盖窄、增不可解释规则、Private 泛化风险高。
- 任何 µm 门限的大规模网格搜索 —— 直接对 Public LB 过拟合。

---

## 7. 从 0.912 继续提升的判断

- **可实现空间**：实验2 已判定 edge_prob **已穿透** → **收窄到 `0.003–0.006`**，主要来自实验1（bonus 兑现稠密区）。
  - 检测融合/gap/division 各 <0.001，非主战场。
- **空间来源**：关联侧"learned 证据利用率"（motion_relink↔edge blend 接驳）＞验证/校准；**不是**检测、ILP 权重、division。
- **可能只是 Public 噪声**：单一 specimen 上、或幅度 <0.002 的变化；µm 门限小数点级微调尤甚。判据：跨 44b6_/6bba_ 一致，且看 adj 而非裸 jaccard。
- **Private 稳定性**：①上线本地 summarise；②每 knob 按两 specimen 分别报告，只接受两组都不降；③冻结当前 OFF/死参不要顺手打开（未经跨分布验证）；④保持 checksum + DeepCenter epoch 锁；⑤优先可解释单调 knob(bonus 权重)而非魔数门限。

---

## 附：关键代码位置速查

| 事项 | 位置 |
|---|---|
| 检测 8-view TTA patch | Cell 9 `_new` 块 |
| 检测 mean/std 融合(0.475) | Cell 9 ensemble replacement #2 |
| 边融合 low_margin_consensus(0.15/0.35) | Cell 9 ensemble replacement #3 |
| softmax(dim=0) 父维 | predict_unet_transformer.py:456 |
| 候选阈值 0.48 | cfg.threshold（Cell9 patch#5）→ predict:465 |
| ILP 目标 −1.0*edge_prob | predict:555-564 |
| motion_relink 整体替换 | Cell 11:2655-2658；cost:2770 |
| gap 钳制 min(_,1) | Cell 11:1911 |
| safe divisions（唯一 division 源） | Cell 11:2257-2359；调用 2696 |
| min_track_len=6 过滤 | Cell 11:2407 |
| linefit smooth(0.8) | Cell 11:2486+ |
| DeepCenter gate（span≥8.5µm synthetic） | Cell 11:2037-2059；启用 Cell4；过时注释 Cell5:248 |
| 本地打分器 summarise | src/biohub_tracking/metrics.py:385 |
| RUN_OUTPUT_DIAGNOSTICS 死变量 | 定义 Cell5:182，无引用 |

---

## 8. 实验结果日志（`src/v8_two_seeds_local_eval.ipynb`）

> ⚠️ **train 泄漏**：primary/secondary 在 199 train 上训过，这 40 视频模型见过 → **绝对分乐观**
> （raw adj 0.9255 > Public LB 0.912 即征兆）。只用**实验间 Δ + 按 embryo 一致性**决策，不看绝对分。

### 实验0 + 实验2（已跑，1 次运行，BONUS=1.0 基线）

40 视频 held-out train（20/specimen，seed=0）：

| 指标 | A raw-ILP（后处理前） | B final（后处理后） | Δ(B−A) |
|---|---|---|---|
| score | 0.9255 | 0.9188 | −0.0067 |
| edge_J | 0.9215 | 0.9085 | **−0.0130** |
| adj | 0.9255 | 0.9148 | **−0.0107** |
| div_J | 0.0000 (0/0/29) | 0.0405 (TP3/FP45/FN26) | +0.004(权重后) |
| node_recall | 0.9846 | 0.9813 | −0.0033 |

**按 embryo（adj）**：raw 44b6=0.9480 / 6bba=0.9170；final 44b6=0.9198 / 6bba=0.9129
→ **后处理伤稠密 44b6 (−0.028) 是稀疏 6bba (−0.004) 的 7×**（扛得住泄漏的结构性信号）。

**结论**：
1. **实验2 = edge_prob 100% 穿透**（743034/743034）→ dual-seed edge blend **无缺陷**，无需回填。
2. 整套 Cell-11 后处理在本地净负 −0.0107 adj，raw ILP 图（完全用 learned 边）反而更好 → 印证 §0：
   motion_relink 整体替换 learned 边在倒扣分。**但 Δ 本身被 train 泄漏偏置**（raw 最过拟合），不能直接判 test
   上后处理有害；能扛泄漏的是 **44b6/6bba 不对称** → motion_relink relaxed 10µm 门在稠密场过宽。
3. safe-div：TP3/FP45（精度 6%、召回 10%），本地净 +0.004，低权重边际、FP 重。

### 实验1（motion_relink bonus sweep）—— ✅**已跑（1.0/1.5/2.0），方向证实但增益不足**

| bonus | adj | Δraw | 44b6 adj | 6bba adj | div_J(TP/FP/FN) | **score**=adj+0.1·divJ |
|---|---|---|---|---|---|---|
| raw-ILP(→∞极限) | 0.9255 | — | 0.9480 | 0.9170 | 0(0/0/29) | 0.9255 |
| final b=1.0 | 0.9148 | −0.0107 | 0.9198 | 0.9129 | 0.0405(3/45/26) | 0.9188 |
| final b=1.5 | 0.9151 | −0.0104 | 0.9207 | 0.9130 | 0.0270(2/45/27) | 0.9178 |
| final b=2.0 | 0.9162 | −0.0093 | 0.9222 | 0.9139 | 0.0270(2/45/27) | 0.9189 |

**结论**：
1. **方向证实**：adj 随 bonus **单调↑**（0.9148→0.9151→0.9162），两 specimen 都不降，收益集中在稠密 44b6
   （+0.0024＞6bba +0.0010）→ 印证"motion_relink 覆盖 learned 边扣 adj、learned 边主救稠密 swap"。
2. **但增益太小 + 被 division 抵消**：b=1→2 adj 只 +0.0014（缺口只收回 ~13%）；且 bonus 调高把 1 个真 division
   重连成单轨（TP3→2）→ **score 在三档几乎持平（0.9188/0.9178/0.9189，b=2 仅 +0.0001）**。adj 的涨分被 div 吃掉。
3. **量纲问题**：cost=`motion(µm)+0.05raw−BONUS·prob`，prob∈[0,1]，BONUS=2 最多 −2，压不过稠密区几 µm 的运动 cost 差。
4. **判据**：未过 +0.002 门槛、score 持平 → **不值得单独提交 LB**（几乎必回 ~0.912 噪声内）。
- **下一步（零成本）**：默认 sweep 已扩到 `1.0,2.0,3.0,4.0,6.0`，先看 adj 是否继续爬过线、某 specimen 是否掉、
  div 是否继续失血。若很快 plateau（~0.916-0.917）→ bonus 路饱和 → 转**实验1b**：改 motion_relink 为
  **仅在 learned prob 低时才覆盖 ILP 边**（高置信 learned 边保留），精准治稠密 swap 且不误伤 division。

# exp_062 — Mutual-best edge association on the frozen 0.947 pipeline

Status: **v3 — CONSENSUS.** Codex returned **PASS** at the strategy level on 2026-09-24
(`docs/research/exp062_codex_challenge_v3.md`): *"Strategy-level CONSENSUS for one unchanged
mutual-best β = 0.20 probe. The two outstanding design corrections are resolved."*
**This CONSENSUS does not authorize launch or leaderboard submission.** Next gates: build →
one scoped implementation/admission review → snapshot smoke → budget reservation → ONE
user-authorized launch → separately authorized submission.
Author: Claude Code, 2026-09-24. Parent: `repro_059_public_0947_exact_copy` (Public LB **0.947**,
submission 56313491).

Lineage: v1 → Codex REVISE (`exp062_codex_challenge_v1.md`, 4 CORRECTNESS + 2 VERIFICATION-DEPTH)
→ v2 consolidated correction → Codex REVISE (`exp062_codex_challenge_v2.md`: five of six round-1
findings **fixed**; one left open; one **newly introduced** defect) → **v3 → Codex PASS**
(`exp062_codex_challenge_v3.md`), no blocking correctness defects, one non-blocking
verification-depth qualification carried into §3.

### What v3 fixes (round 2)

1. **[was CORRECTNESS, newly introduced by v2] The calibration account was wrong.** v2 claimed the
   bonus is applied to re-standardised *harmonic-fusion* logits scaled *per source*. Verified
   against the parent: `forward_scale` reduces `dim=1` of `(1, n_src, n_tgt)` → `(1, 1, n_tgt)`, so
   it is **per target, across sources**; the `[0.5, 2.0]` clamp is on the **ratio**, not on the
   scale (which is `clamp_min(1e-4)`); and fusion is followed by a **secondary-model blend** before
   `raw` is assigned. v2 stopped tracing the tensor too early. See §2.
2. **[round-1 finding 2, still open] Cache isolation was unspecified — and the parent has a real
   resume-signature collision.** `_inference_resume_env_keys` is a fixed 13-key list that does
   **not** contain the new variables, so a candidate run can compute the **same** resume signature
   as the control, skip inference and replay the control's predictions. See §4.1. This would have
   produced a silent false null and burned an LB slot on a duplicate 0.947.
3. The parent-SHA guard is now **actively cleared** in candidate mode rather than merely absent
   from source (§4.2), per Codex's point that source absence does not establish process-environment
   absence.

### What changed from v1, and why

Every item below was a v1 defect. Three were independently re-verified against the repository
before being accepted; all three were genuine.

| v1 claim | status | v2 |
|---|---|---|
| "All four prior probes moved division; this is the first edge lever" | **FALSE** — exp_055 was edge-side (`adjusted_edge_delta` +0.0033/+0.0189, `division_jaccard` unchanged at 0.2) and still returned 0.000 | §0 motivation **rebuilt** on insertion point, not metric term |
| "best choice of its source (column) and of its target (row)" | **REVERSED** — the tensor is `[n_src, n_tgt]` (`predict_unet_transformer.py:452`) | §2 axes corrected and pinned to the source |
| Gate 5: "a non-mutual pair's logit is strictly lower" | **FALSE** — col-best-only gains `0.8β`, row-best-only gains `0.3β` | §6 replaced by the four-row truth table |
| "PP-sweep disabled as in exp_060's lb-submit kernel" | **FALSE** — that sweep ran and re-selected tight55 | §7 budget rebuilt; sweep retained |
| Auto-escalate to β = 0.40 on a null | unjustified | §8 escalation removed |
| "Only transport with a proven hidden-rerun record" | overstated | §1 downgraded to "closest successful minimal-change precedent" |
| "E survived the A–E series" | inferred from an env-var name | §2 downgraded to unverified context |
| Metric as a "0.9/0.1 convex mixture" | imprecise | §0 states the actual formula |

---

## 0. Motivation — the honest version

Four consecutive causally-isolated probes returned **zero** displayed Public LB movement:

| experiment | intervention | pipeline stage | LB | delta |
|---|---|---|---|---|
| exp_055 | original-score joint cut-and-reconnect | **post-smoothing graph repair** | 0.942 | 0.000 |
| exp_057 | motion EMA | **post-solve smoothing** | 0.944 | 0.000 |
| exp_060 | safe-div threshold 0.20→0.18 | **division accept gate** | 0.947 | 0.000 |
| exp_061 | Z-reflection DeepCenter TTA | **division candidate scoring** | — | never scored |

**v1 claimed the common factor was the division term. That was wrong.** exp_055 was an *edge*
intervention: its entire frozen-proxy gain (+0.0148537) was adjusted-edge, with `division_jaccard`
unchanged at 0.2 in every specimen block, and the LB still did not move. Our own A0 ceiling audit
says so explicitly: *"the big edge lever = fragmentation, already targeted by exp_055 joint repair
which was LB-flat"* (`STATE.json.exp057_a0_part1.key_findings`).

**The actual common factor is the insertion point.** All four acted **downstream of the ILP
solve** — repairing, smoothing, or re-gating a graph the solver had already produced. None of them
changed the edge probabilities the solver *optimizes over*.

Mutual-best acts **upstream of the solver**: it modifies `raw` edge logits at
`predict_unet_transformer.py:454`, before the activation at 456 and before the candidate list is
built at 460–468 and handed to the ILP. It therefore changes the feasible set and the objective the
solver sees, not the solver's output.

**This is a weaker argument than v1's, and it should be read as such.** It is a hypothesis about
*where* in the pipeline remaining headroom might be reachable, not a claim that the lever is
untried or that the metric weights guarantee visibility. Specifically:

- The official score is **`adjusted_edge_jaccard + 0.1 × division_jaccard`** — not a 0.9/0.1 convex
  mixture. The asymmetry is real but the coefficients **do not** establish remaining headroom.
- The A0 audit in fact gives **division the largest optimistic headroom** (perfect division +0.085
  vs all-edge-FN +0.045). Division is not dismissed and option B remains live (§8, Appendix).
- exp_055 is direct evidence that **edge-side work can also be LB-flat**.

Context that bounds the decision: 0.947 is **outside the top 200** (rank-200 cutoff 0.949, LB top
0.975); the competition closes **2026-09-29 23:59**. Recon:
`docs/research/public_frontier_recon_2026-09-23.md`.

## 1. Parent and deployment substrate

- **Parent:** `repro_059_public_0947_exact_copy`, submission SHA256
  `d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60`, Public LB 0.947.
- **Substrate:** a **single-config variant notebook** whose own `submission.csv` *is* the candidate,
  submitted with `competition_submit_code`.

exp_060's lb-submit kernel (submission 56361673, COMPLETE at 0.947) is the **closest successful
minimal-change deployment precedent** in this project. It is *not* the only working transport —
`repro_059` (56313491), `exp_057` (56281129) and `exp_055` (56261282) also returned scores via code
submission. What the exp_061 post-mortem actually establishes is narrower and still decisive: five
submissions failed across two static-copy kernels and three **bespoke deployment adapters** with
custom watchdogs, caches and atomic-publication layers. **exp_062 adds no deployment machinery.**

## 2. The intervention

Inserted immediately before the edge activation in `predict_unet_transformer.py`. The anchor block
(lines 454–458 of our reference copy) exists verbatim, confirming portability:

```python
raw = edge_logits_pair[0]                       # (n_src, n_tgt)  -- line 452 annotates the shape
_lb_mode = os.environ.get("BIOHUB_LB_SCORING_MODE", "none")
_lb_beta = float(os.environ.get("BIOHUB_LB_SCORING_BETA", "0"))
if _lb_mode in {"relative_rank", "mutual_best"}:
    _lb_col_prob = torch.softmax(raw.float(), dim=0)
    _lb_row_prob = torch.softmax(raw.float(), dim=1)
    _lb_col_best = torch.argsort(torch.argsort(-_lb_col_prob, dim=0), dim=0) == 0
    _lb_row_best = torch.argsort(torch.argsort(-_lb_row_prob, dim=1), dim=1) == 0
    _lb_mutual   = _lb_col_best & _lb_row_best
    _lb_rank_bonus = (_lb_beta * _lb_col_best.float()
                      + 0.50 * _lb_beta * _lb_row_best.float()
                      + 0.50 * _lb_beta * _lb_mutual.float())
    if _lb_mode == "mutual_best":
        _lb_rank_bonus = _lb_rank_bonus - 0.20 * _lb_beta * (~_lb_mutual).float()
    raw = raw + _lb_rank_bonus.to(raw.dtype)
if cfg.edge_activation == "softmax":
    probs = torch.softmax(raw, dim=0).cpu().numpy()
else:
    probs = torch.sigmoid(raw).cpu().numpy()
```

### Axis semantics — corrected and pinned to the source

`model.predict_edges(...)` returns `(1, n_src, n_tgt)` (`predict_unet_transformer.py:452`), so after
`raw = edge_logits_pair[0]` **rows are sources and columns are targets**:

| expression | reduces over | meaning |
|---|---|---|
| `softmax(raw, dim=0)` / `_lb_col_best` | **sources** | *which source is best for this target* |
| `softmax(raw, dim=1)` / `_lb_row_best` | **targets** | *which target is best for this source* |

The parent's own activation is `softmax(raw, dim=0)` (line 456) — i.e. the parent already normalises
over **sources**. The target-side competition (`dim=1`) is the axis the parent does **not**
normalise over, and is where this prior adds information.

**Activation branch — resolved, not assumed.** `edge_activation` is declared
`edge_activation: str = "softmax"` (`predict_unet_transformer.py:72`) and the parent notebook
**never overrides it** (no occurrence of `edge_activation` anywhere in its source). The parent is
therefore confirmed on the **softmax** branch and the `sigmoid` branch is unreachable in our
configuration. This materially de-risks what v1 could only list as an open hazard — but the branch
is still asserted at runtime (§6.6), because a silent switch would change the meaning of β.

### What `raw` actually is — corrected in v3

`raw` is **not** the network's forward logits, and v2's account of it was wrong in three ways.
Traced through the parent (`repro_059` snapshot, code cell 2):

| step | lines | what happens to `edge_logits_pair` |
|---|---|---|
| 1. bidirectional harmonic fusion | 1345–1363 | reverse logits transposed and aligned, fused as a weighted harmonic mean of **source-axis** softmax probabilities (reverse weight 0.15), `log`-ed, then re-standardised to the forward mean/scale |
| 2. **secondary-model blend** | 1187–1226 | `low_margin_consensus`: a **per-target** `blend_weight` from the primary's top-2 margin and whether primary and secondary pick the **same parent**, then `(1−w)·primary + w·secondary_for_mix` |
| 3. optional temperature | 1228–1230 | re-scales about the mean if `secondary_mix_temperature != 1.0` |
| 4. | 1232 | `raw = edge_logits_pair[0]` — **this** is what the patch sees |

Three corrections to v2:

- **The scale is per target, not per source.** `edge_logits_pair.float().std(dim=1, keepdim=True)`
  on `(1, n_src, n_tgt)` reduces the **source** axis, giving `(1, 1, n_tgt)` — one statistic per
  target, computed across sources.
- **The `[0.5, 2.0]` clamp is on the ratio**, not on the scale. The scales themselves are only
  `clamp_min(1e-4)` / `clamp_min(0.0001)`.
- **Fusion is not the last step.** The secondary blend (step 2) runs *after* it, so `forward_scale`
  alone does not describe the scale of the tensor receiving the bonus.

So β = 0.20 is expressed in units of a **twice-restandardised, secondary-blended logit whose
per-target scale is set by a chain we do not control**. A borrowed β is even less transferable than
v2 supposed. Telemetry must therefore separate **intermediate-scale** statistics (`forward_scale`,
`blend_weight`) from **final-`raw`** statistics, and it is the latter that governs what β means
(§6.7).

### A mechanism refinement that falls out of the same trace

Step 2 already computes `torch.softmax(edge_logits_pair[0], dim=0)` and
`topk(..., dim=0)` — i.e. **the best source per target**, plus that choice's top-2 margin and
whether the secondary model agrees on it (lines 1199–1220). That is *the same quantity* as
`_lb_col_best`.

Consequence, stated against my own proposal: the `col_best` term — which carries the **largest**
single weight in the bonus (`β`) — is largely a re-expression of a signal the pipeline already
computes and already acts on. **The genuinely novel information is `_lb_row_best`: the best target
per source.** Nothing upstream normalises over, or takes an argmax along, the target axis.

This is a sharper and less flattering reading than v2's. It does not change the decision to run one
β = 0.20 probe of the published form — altering the weighting would make the result non-comparable
to the only prior art we have. Codex confirmed the reading at PASS, with two qualifications that
are recorded here rather than argued with:

- **It is reused ranking information, not mathematical redundancy.** Under the frozen
  `low_margin_consensus` configuration the blend is applied only when both models share the column
  winner and is zero-weighted otherwise; the convex blend preserves a strict shared winner and the
  temperature is 1 — so the final column winner *ordinarily* matches the previously computed one
  (ties and numerical effects qualify exact identity; parent lines 996–1004, 1211–1232).
  **But gating a model blend and explicitly boosting a winner are different transformations:** the
  column bonus still changes probability concentration and potentially candidate admission.
- **[non-blocking, carried forward] A null will not isolate the target-competition contribution.**
  It tests the *whole weighted intervention*. It cannot establish that row/mutual information
  failed, nor that a row-weighted successor would be preferable. The designated successor therefore
  remains **density-adaptive relinking** (§8), not a row-weighted β variant.

### Net bonus — the corrected truth table

| pair status | `col_best` | `row_best` | net bonus |
|---|:--:|:--:|---:|
| mutual | 1 | 1 | **`2.0 β`** |
| column-best only (best source for its target) | 1 | 0 | **`0.8 β`** |
| row-best only (best target for its source) | 0 | 1 | **`0.3 β`** |
| neither | 0 | 0 | **`−0.2 β`** |

At β = 0.20 the maximum bonus is 0.4 logits and the largest within-column spread is 0.44, an odds
multiplier of ≈1.55 under softmax. **Only "neither" pairs are penalised.** v1's required
monotonicity gate asserted the opposite and would have failed against a correct implementation.

### Mechanism — what it is, and what it is not

Codex read the parent source and established that this is **not mathematically redundant** with the
existing bidirectional harmonic fusion: reverse logits are transposed, aligned and normalised along
the **same source axis** as forward logits, fused at reverse weight 0.15, and never enforce
simultaneous row/column winners (parent notebook code cell 2, source lines 1345–1363). So the prior
does add target competition within each source.

**But it reinforces the existing fused ranking rather than supplying independent evidence.** It can
strengthen a confidently wrong winner, disadvantage a legitimate second daughter (a real risk on a
cell-division task), and it depends on across-column logit calibration. The correct description is
a **rank-sharpening heuristic** — not a ratio test, and not an established anti-hijacking mechanism.
v1's "classical mutual nearest-neighbour / ratio test" framing overclaimed.

**Pedigree — unverified context, not efficacy evidence.** `haideptry`'s notebook carries
`BIOHUB_LB_EXPLORATION_ID = "e-mutual-best"` and `yudaiyamauchi` published an A–E series on this
axis. That an identifier names E proves **neither** that E beat A–D **nor** that any measured
comparison occurred. Low vote counts establish neither novelty nor limited adoption, and absence
above a 0.949 cutoff does not by itself discredit a 0.948 claim. β = 0.20 is **a published starting
point**, nothing more.

## 3. Hypotheses

> **H1 (primary, LB-falsifiable).** Adding the mutual-best rank prior at β = 0.20 to the edge logits
> of the frozen 0.947 pipeline, with every other parameter byte-identical to `repro_059`, changes
> the Public LB score by at least +0.001 relative to 0.947.

Falsified by a Public LB score ≤ 0.947.

**H1 is an operational hypothesis about the *displayed* score**, per Codex round 2. Equality at
three decimals does not scientifically falsify every possible underlying benefit; it establishes
only that the intervention is not worth carrying at the resolution the competition reports. That is
the decision we actually need to make, and this proposal claims nothing stronger.

> **H2 (execution, not efficacy).** The patch *ran*: the anchor matched exactly once, the patched
> region hash matches the expected value, and `_lb_rank_bonus` was non-zero on at least one frame.

> **H3 (effect, measured at three levels independently).** The intervention propagated: (a) edge
> **probabilities** differ from the control; (b) the **candidate set** above `cfg.threshold` differs;
> (c) the **final graph** differs from `d3453380…`.

**H3 deliberately does not require mutual-best *status* to change.** Per Codex: an effective
confidence adjustment can preserve every winner while still altering probabilities and the
candidate set. Each of (a), (b), (c) is recorded separately so a null at one level does not mask a
change at another. H2 failing is a **defect**; H3 failing with H2 passing is a **valid null**.

## 4. Deployment design — two kernel versions of one notebook

v1 proposed "two arms in one kernel" while claiming to follow the single-config precedent; those
are incompatible. v2 split them. v3 keeps that split and adds the isolation contract Codex found
missing.

**One notebook. Two kernel versions. Environment is the only difference.**

| version | `BIOHUB_LB_SCORING_MODE` | β | `BIOHUB_EXP062_EXPECT_PARENT_SHA` | role | submitted? |
|---|---|---|---|---|---|
| **k1** | `none` | 0.00 | set to `d3453380…` | real-pipeline parity control | **never** |
| **k2** | `mutual_best` | 0.20 | **actively cleared** | candidate | **yes, once** |

k1 proves on the real GPU pipeline that the notebook is **inert** when the prior is off — that the
insertion perturbs nothing through any route other than the intended bonus. k2 is the deliverable
and runs **one config only**, exactly the exp_060 lb-submit shape.

### 4.1 Cache isolation — the defect this section exists to close

**The parent's resume machinery is blind to the new variables, and that is not a hypothetical.**
`_inference_resume_env_keys` (parent cell 2, line 1669) is a fixed 13-key list:

```
BIOHUB_DET_THRESHOLD, BIOHUB_SECONDARY_EDGE_WEIGHT, BIOHUB_SECONDARY_DETECTION_WEIGHT,
BIOHUB_SECONDARY_LINK_MODE, BIOHUB_SECONDARY_MIX_TEMPERATURE, BIOHUB_SECONDARY_LOW_MARGIN_MAX,
BIOHUB_DUAL_SEED_EDGE_THRESHOLD, BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION,
BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT, BIOHUB_BIDIRECTIONAL_FUSION_MODE, BIOHUB_EDGE_FEATURE_TTA,
BIOHUB_SECONDARY_EDGE_FEATURE_TTA, BIOHUB_SECONDARY_EDGE_FEATURE_TTA_WEIGHT
```

`_test_prediction_signature` (line 1670) hashes exactly
`{key: os.environ.get(key) for key in _inference_resume_env_keys}` — so
**`BIOHUB_LB_SCORING_MODE` and `BIOHUB_LB_SCORING_BETA` do not enter the signature at all.**
If working state from k1 is visible to k2, then `_test_prediction_ready` is true (line 1672),
inference is **skipped entirely** (1674–1680), and k2 replays k1's cached predictions. The
candidate would emit the control's output while every other gate passed.

This is the same silent-false-null class as Risk 1, reached by a different route, and it would have
burned an LB slot on a duplicate 0.947. That the parent's resume state is real and persisted is
directly evidenced by `biohub_live_resume/test_prediction_state.json` in the collected exp_061 v5
kernel output.

**Fix — two independent layers, both required:**

1. **Signature correctness (primary).** A `# exp062` line appends `BIOHUB_LB_SCORING_MODE` and
   `BIOHUB_LB_SCORING_BETA` to `_inference_resume_env_keys`, so mode and β enter the test-prediction
   signature *and* every downstream signature derived from the same key list — including the
   validation-reuse path (parent lines 3290–3295), which inherits it. This makes the cache
   *discriminate* rather than merely be absent, which is the durable fix.
2. **Fresh state (belt and braces).** k1 and k2 are separate kernel versions with no carried-over
   working directory, and the notebook asserts at startup that no pre-existing
   `test_prediction_state.json` carries a signature computed under a *different* mode/β. If one is
   found, it **fails closed** rather than silently resuming.

Layer 1 alone is the correct engineering fix; layer 2 exists because a silent cache hit is
unobservable in the output and we have already been burned twice by unobservable no-ops.

**Insertion point, confirmed by Codex at PASS:** append **immediately after the list definition
(line 1669) and before the first hash computation (line 1670)**. Codex traced the propagation
through the parent and it covers every candidate-reuse path:

| parent cell-2 lines | signature chain |
|---|---|
| 1669–1672 | extended list → test signature → inference-reuse decision |
| 3171–3172 | base / final-output reuse **also** requires the test signature |
| 3290, 3686, 3723 | test signature → validator prediction → validator base and PP-sweep signatures |
| 3783 | final signature includes test, postprocessing and sweep signatures |

Two signatures do **not** inherit the keys — standalone postprocessing (289–296) and the
disabled-validator sentinel (3345) — and Codex confirmed neither opens an uncovered candidate-reuse
path: output reuse separately checks the test signature, and sweep reuse requires enabled
validation.

**⚠ Trap that would have defeated the naive alarm.** Parent **line 1675 restores the historical
`predict_seconds` from the cached state on a cache hit**, so the *reported* prediction time looks
normal. The cache-hit alarm must therefore use **actual measured elapsed wall-clock**, never the
reported value.

**Gate:** telemetry records `resume_signature_inputs_include_exp062_keys: true`, whether
`_test_prediction_ready` was true or false, and the **independently measured** inference wall-clock.
Legacy state whose signature scheme is unrecognised is **rejected fail-closed**, not ignored.

### 4.2 The parent-SHA guard must be cleared, not merely absent

The historical-output equality assertion is gated on `BIOHUB_EXP062_EXPECT_PARENT_SHA`, set only in
k1. A hidden rerun operates on **different input data**, so requiring the historical public CSV hash
there would fail-closed on correct code (Codex round-1 finding 2).

Per Codex round 2, **absence of an assignment in the notebook source does not establish absence from
the process environment.** So k2 does not rely on absence: it executes
`os.environ.pop("BIOHUB_EXP062_EXPECT_PARENT_SHA", None)` in candidate mode and then **asserts the
variable is unset** before inference. The builder additionally asserts the k2 source contains no
assignment to it. Source-level and runtime-level, both.

**k2 retains every ordinary current-input integrity check** — graph validity, consecutive-frame and
lineage-degree audits, nonfinite checks, effective-config drift guard. Only the *historical
public-output equality* check is skipped, because only that one is meaningless on hidden data.

### 4.3 PP-sweep

Both versions retain the parent's adaptive PP-sweep. v1 of this proposal claimed exp_060's
lb-submit kernel disabled it; it did not — the sweep ran and re-selected `tight55`
(`STATE.json.exp060_0p18_lb.run_completed`). Retaining it keeps the deployment byte-faithful to the
precedent and removes a gratuitous difference.

## 5. Risks

**Risk 1 — the patch silently does not apply. (Highest.)**
The upstream implementation inserts by string replacement and, on an anchor miss, merely prints
`Note: Mutual-Best anchor found N times` and **continues unpatched** — producing an arm identical to
the parent that we would misrecord as a null. This is the "false verified-null" class Codex raised
as exp_061 admission v1 finding #2.
*Mitigation:* anchor match count asserted `== 1`, **fail closed** (raise) on any other count, before
any inference begins; the patched source is re-compiled and its region hash recorded (H2).

**Risk 1b — a silent cache hit. (Raised in v3.)**
The parent's resume signature does not include the new variables, so without §4.1 the candidate run
would replay the control's predictions and emit the control's output with every gate green. Closed
by §4.1 layers 1 and 2 plus the wall-clock alarm; listed separately because it is a *different*
failure route to the same indistinguishable outcome as Risk 1.

**Risk 2 — a real regression.**
The prior acts upstream of the solver, so its effect is amplified by the ILP rather than applied to
a finished graph. A poorly calibrated β can plausibly cost more than 0.001. Rollback is instant
(§8) and the stop rule is strict.

**Risk 3 — the prior is empirically redundant.**
Per §2 it reinforces the existing fused ranking rather than adding independent evidence. A null is a
genuinely likely outcome and is **not** evidence that the upstream insertion point is barren.

**Risk 4 — β is borrowed, not derived, and expressed in a scale we do not control. (Corrected in v3.)**
Per §2, `raw` is a **twice-restandardised, secondary-blended** logit whose per-**target** scale
comes from a chain we do not control (harmonic fusion → `low_margin_consensus` blend → optional
temperature). v2 described this as a single per-source fusion scale and was wrong. A β borrowed
from another author's run is therefore not obviously comparable to ours even though both pipelines
descend from the same upstream. This is **not** mitigated by anything in this design — it is
accepted, recorded, and is the reason the stop rule refuses an automatic β sweep (§8).
*Partial mitigation:* telemetry records final-`raw` statistics separately from intermediate
(`forward_scale`, `blend_weight`) statistics, so a successor can reason about β rather than guess
(§6.7).

**Risk 5 — the `sigmoid` branch. (Downgraded in v2 after verification.)**
`edge_activation` defaults to `"softmax"` (`predict_unet_transformer.py:72`) and the parent notebook
never overrides it, so the `sigmoid` branch — under which a logit bonus would shift absolute
probabilities against the `probs[i, j] > cfg.threshold` filter at line 465 rather than a normalised
ranking — is unreachable in our configuration. Retained as a **runtime assertion** (§6.6) rather
than a design hazard.

**Risk 6 — deadline.** Five days remaining as of 2026-09-24. §7 budgets the whole plan, not just
the first run.


## 6. Local gates — all zero-GPU, all executable

1. **Builder parity guard.** Stripping `# exp062`-marked lines reproduces the parent notebook
   byte-for-byte.
2. **β = 0 inertness.** `_lb_rank_bonus` is **exactly** zero (not merely small) and `raw` is
   returned unmodified, asserted on the tensor, not on a printed value.
3. **Axis semantics through the actual patched source.** Per Codex answer 1, a constructed matrix
   alone is insufficient: the test imports the *patched* module and drives the real activation block
   with an **asymmetric rectangular** matrix (n_src ≠ n_tgt) containing a known mutual-best pair,
   plus **ties**, a **single-source** case and a **single-target** case, asserting which entries
   receive `col_best` / `row_best` / `mutual` and that rows are sources.
4. **Bonus truth table.** The four rows of §2 asserted exactly, for at least two β values.
5. **Anchor fail-closed.** With a deliberately corrupted anchor the run **raises**; with a duplicated
   anchor it also raises.
6. **Activation branch.** Tests run under both `softmax` and `sigmoid` so the patch is correct
   either way, **and** the run asserts at runtime that the effective branch is `softmax` — the
   verified parent configuration — recording it in telemetry. A silent switch would change the
   meaning of β (Risk 5).
7. **Calibration telemetry, separated by stage.** Final-`raw` statistics (mean/std/percentiles per
   dataset) are recorded **distinctly from** intermediate `forward_scale` and `blend_weight`
   statistics, so the scale β actually acts on is not confused with an earlier one (Risk 4).
8. **Resume-signature discrimination.** An executable test asserts that two environments differing
   only in `BIOHUB_LB_SCORING_MODE` / `BIOHUB_LB_SCORING_BETA` produce **different**
   `_test_prediction_signature` values, and that a state file written under one mode is **rejected**
   under the other (§4.1). This is the zero-GPU proof that the cache discriminates.
9. **Parent-SHA gating, source and runtime.** The k2 notebook source is asserted to contain no
   `BIOHUB_EXP062_EXPECT_PARENT_SHA` assignment, **and** k2 is asserted to `pop` the variable and
   verify it unset before inference (§4.2).
10. **Snapshot smoke** against the immutable snapshot.

### No local-proxy gate — stated as what it is

This is a **resource decision**, not a claim that the proxy is worthless. Honest accounting of the
evidence, corrected from v1:

- **exp_055 is genuine transfer-failure evidence**: frozen-proxy +0.0148537, displayed LB gain 0.000.
- **exp_057 is not**: it explicitly skipped proxy scoring; its 3,714 changed edges measure
  *activity, not quality*.
- The third-party `evgendvorkin` evolution table is **independently unverified** — Codex could not
  retrieve the notebook through web retrieval, and our reading came from a local pull.

So there is **one** solid transfer failure, not three. A proxy pass costs GPU hours we would rather
spend on a second distinct mechanism before the deadline. **Consequence, stated plainly: exp_062
has no pre-LB quality estimate at all.** Correctness and graph-integrity gates are retained; the
Public LB is the only quality instrument, per the standing 2026-09-18 user policy.

## 7. Budget — the whole plan

| item | GPU | note |
|---|---|---|
| kernel version **k1** (control, β = 0) | ~1.3 h | includes the parent PP-sweep, as exp_060 did |
| kernel version **k2** (candidate, β = 0.20) | ~1.3 h | the submitted version |
| **exp_062 total** | **~2.6 h** | reserved as 3.0 h |
| contingency for one successor lever | ~1.3 h | *not* reserved here |

Remaining 20.398674 h, of which **14.398674 h are unprotected** (six protected hours preserved).
A 3.0 h reservation is inside `max_single_experiment_hours` 4.0 and leaves ~11.4 h unprotected for
successors. **Submissions: exactly one**, separately authorized, remote cap checked first
(authenticated cap 5/day).

**Artifacts:** `submission.csv` per version; `exp062_telemetry.json` recording anchor match count,
patched-region hash, effective activation branch, per-version output SHA, frames with non-zero
bonus, and the three H3 levels (probability delta, candidate-set delta, final-graph delta); gated
`metrics.json` (`exp062_mutual_best_integrity_passed`).

## 8. Stop rule and rollback

Pre-registered against 0.947. **No automatic escalation** (v1's β → 0.40 rule is removed).

| k2 Public LB | reading | action |
|---|---|---|
| **≥ 0.948** | H1 supported | adopt as new parent; record; any further β probe requires its own justification and authorization |
| **== 0.947** | **uninformative between several causes** | **close the probe.** Move to density-adaptive relinking |
| **≤ 0.946** | H1 falsified at displayed resolution | **revert immediately**, keep repro_059 0.947; move to density-adaptive relinking |

Density-adaptive relinking is the designated successor but is **not authorized by this document**:
it requires its own proposal, its own challenge round and its own launch authorization.

**Why `== 0.947` no longer licenses a bigger β.** Per Codex finding 4, changed predictions with an
unchanged displayed score can mean beneficial/harmful **cancellation**, changes **outside the sparse
annotations**, or **rounding** — not necessarily "the effect is too weak". Equal three-decimal
scores also do **not** establish an absolute delta below 0.0005. A follow-up β would need a fresh
argument, not an automatic rule.

**If k2's output is byte-identical to the control**, do **not** submit at all — it would
duplicate a known 0.947 and consume a slot for no information.

**Rollback:** `BIOHUB_LB_SCORING_MODE=none` restores the parent byte-for-byte; the builder guard
guarantees the notebook strips back to the parent. No state outside the kernel is mutated.

**Hard stop on this lever:** at most the two kernel versions and one submission above. If it is not
clearly positive, it closes.

## 9. Governance — the bounded gate, as Codex amended it

Codex **accepted** the bounded-gate contract with amendments, which this version adopts verbatim:

- One consolidated strategy correction (**this document**), then **one** scoped
  implementation/admission review against the exact snapshot.
- **Block** on concrete correctness, leakage, provenance, fail-closed, graph-validity or budget
  defects.
- **Record without blocking**: speculative efficacy and additional verification depth.
- Real-GPU parity and execution evidence live **inside the authorized run** (k1) and
  are required **before submission**, not before launch.
- Re-review covers **fixes and newly introduced defects only** — and, as Codex correctly insisted,
  **a round limit can never make a known defect acceptable.**
- Fresh experiment-specific Codex PASS and separate submission authorization are preserved.

Correction to v1's premise: the record documents **five custom plus four formal** admission rounds
for exp_060, not five in total (`experiments/exp_060_.../formal_admission_status.md:55`).

## 10. What would change my mind

- If the admission review finds the patched module cannot be exercised locally at all, gate 3 is
  unsatisfiable and the axis risk becomes unmitigated — that would be a blocking defect.
- If the runtime assertion finds the effective activation branch is **not** `softmax`, the verified
  premise in §2 is broken, the borrowed β = 0.20 becomes much less defensible, and the probe should
  be re-derived before launch rather than submitted.
- If k1 does **not** reproduce `d3453380…`, the insertion is not inert and the experiment stops
  there, before any submission.
- If k2's measured inference wall-clock is near zero, or `_test_prediction_ready` was true, treat
  the run as a **cache hit and not a candidate** regardless of what the output looks like — do not
  submit it (§4.1).

---

## Appendix — deliberately out of scope

- **Density-adaptive relinking** (recon lever 2) is the **designated successor**, per Codex's
  recommendation, not a bundle-in. Bundling would repeat the causal-isolation failure that
  `repro_059`'s own +0.003 suffers from (`repro_059/PROVENANCE.md` §5).
- **Option B** (larger 0.15/0.12 safe-div move) remains **live**. Codex explicitly declined to
  dismiss division categorically, and the A0 audit gives division the largest optimistic headroom.
  It is sequenced after density-adaptive, not cancelled.
- **DivNet mitosis gate** (recon lever 3): a larger integration and a model-provenance commitment.
- **No new deployment machinery.** exp_061's five failed transports settled that.

# exp_061 — DeepCenter repair-heatmap TTA probe (Z-reflection + XY-D4 repair)

Record type: versioned strategy proposal.
Status: **v5 — CONSENSUS (Codex `gpt-6-astra`, 2026-09-20, after REVISE v1–v4; see
`exp061_codex_challenge_v5.md`). Strategy is AGREED.** Implementation is NOT yet authorized — it
still requires a build on the repro_059 snapshot with `admission.require_codex_review: true`, a
fresh Codex *admission* PASS, local tests + snapshot smoke, and a budget reservation before any
user-authorized launch. No leaderboard submission authorized here.
Author: Claude Code. Date: 2026-09-20.
Parent: **repro_059_public_0947_exact_copy** (Public LB **0.947**, authenticated submission
56313491). This is **option A** the user selected on 2026-09-20 after exp_060 returned a Public-LB
null (0.18 arm == 0.947).
Challenge history: `exp061_codex_challenge_v1.md` (REVISE; 3×P1 + 5×P2) → v2;
`exp061_codex_challenge_v2.md` (REVISE, narrowed; confirmed P1-1/P1-3/P2-6/P2-7/P2-8 resolved) →
v3; `exp061_codex_challenge_v3.md` (REVISE, cleanup-only: transforms confirmed correct, 5
consistency/accounting fixes, no reopened findings) → **v4**. See §14/§15/§16 resolution tables.
Code anchors: **N** = `.private/current/exp060_deepcenter_safe_div_threshold_sweep.ipynb`
(cell 2 = base pipeline, cell 3 = exp_060 harness). Line numbers are extracted-source lines.

> **Standing reminder (user, 2026-09-20):** after this experiment reaches its Public-LB result,
> REMIND the user to run **option B** — a *larger* safe-div threshold move (0.15 / 0.12) to clear
> the 3-decimal LB grain that exp_060's 0.02 bracket fell below. Tracked in
> `STATE.json.pending_followup` (ARMED).

---

## 0. One-paragraph summary

The 0.947 parent computes a DeepCenter center-prior **heatmap** per `(dataset,t)` and reads it as
a **pass/fail veto** at exactly **TWO** call sites, in stage order: **gap1** inside
`close_single_frame_gaps` (N cell2:2454), then the **safe_division** accept gate (N cell2:2731).
(`recover_strict_gap2` runs between them but reads no heatmap — it is a downstream stage, not a
veto consumer; N cell2:2497–2632.) Among daughters that survive the safe-div veto, safe-division
ranks by `parent_dist + 0.15*sister_dist` (N cell2:2740–2746), NOT by the heatmap value. exp_060
showed that moving only the safe-division *accept threshold* by ±0.02 does not move the LB at 3-dp.
This experiment instead perturbs the **heatmap itself** by changing the DeepCenter test-time
augmentation (TTA) set — a *shared repair-heatmap intervention* that can change veto eligibility at
gap1 AND safe-division, and hence downstream graph structure (including gap2, which reacts to the
changed gap1 result). It runs **one Kaggle
inference** and replays post-processing from **before the first DeepCenter consumer** under three
pre-registered arms: **`xyonly`** (parent TTA exactly = byte-parity control), **`zon`** (add a
Z-axis reflection of every view), **`xyd4`** (repair the XY group to a uniform 8-view D4 by
*replacing* the duplicated view with the missing anti-diagonal reflection; no Z). It submits the
two experimental arms to the unlimited Public LB via the exp_060-proven per-arm promotion route.
**Honest priors:** (a) this may be another sub-precision null (division is 0.1-weighted; heatmap
changes only flip borderline vetoes); (b) `zon` may *regress* if the DeepCenter checkpoint is not
Z-symmetric — an uncertain symmetry assumption, not an established OOD fact. The value is a cheap,
well-isolated LB read on a genuinely different (upstream, representation-level) lever than
exp_060's accept gate, with `xyd4` as the geometrically better-motivated companion.

## 1. Motivation and why this is a *different* lever than exp_060

- **Division still holds the most headroom** (A0 Part 1: edge layer ~LB-flat). Three
  causally-isolated post-processing edits were LB-flat (exp_055 edge, exp_057 EMA, exp_060 gate).
- **exp_060 moved the accept *gate*; this moves the *heatmap* the gate (and the gap1 veto) read.**
  Lowering the threshold only re-labels candidates already scored by a fixed heatmap. A TTA change
  perturbs the heatmap values, changing which points pass the veto at gap1 and safe-division — a
  representation-level change with an earlier entry point (gap1, before safe-division).
- **We do NOT claim this must exceed exp_060's effect.** Whether a heatmap perturbation moves more
  or fewer borderline vetoes than a 0.02 gate move is unknown a priori; the pre-registered rule
  treats a null as a real, recorded outcome. We also do NOT claim exp_060's +11 forks was
  "necessarily below LB resolution" — public-subset membership and scoring denominators are
  unknown, so that count bounds nothing about LB precision.

## 2. Exact current behavior (authoritative code anchors)

**Heatmap + its consumers (N cell 2):**
- `deepcenter_heatmap_for_frame` (L2089–2139): inner cache `heatmap_cache[key]`, **key
  `(dataset,int(t))` with NO TTA component** (L2092). TTA gated by `BIOHUB_DEEPCENTER_TTA`
  (L2110): original + `flip((-1,))`,`flip((-2,))`,`flip((-2,-1))` (3 XY flips) + `rot90 k∈{1,3}`
  + `transpose(-1,-2)` (main diagonal) + `transpose(rot90(x,1))` (**anti-transpose**, input
  `rot90(tensor,1).transpose(-1,-2)`, inverse `rot90(·.transpose,-1)`, L2124–2126). Geometrically
  the anti-transpose maps to the **X-flip orientation**, but it is a **distinct forward on a
  distinct input tensor** — `model(transpose(rot90(x,1)))` ≠ `model(flip(x,-1))` numerically, so
  it CANNOT be deduplicated against `Vx` (Codex v2 #3). Thus the parent executes **8 forwards**
  producing 7 geometrically-distinct orientations (Ta and Vx share an orientation but are separate
  forwards). All ops are XY-only (dims -1,-2); Z (dim -3) is never transformed. Rot/transpose
  views require
  `tensor.shape[-1]==tensor.shape[-2]` (square XY); the 3 flips always apply. `delta==0.0` hard
  raise at L2129–2130.
- `deepcenter_score_point` (L2142–2178): scores a point against the heatmap; **bypasses (returns
  None / no veto)** when `not USE_DEEPCENTER_VETO or detector_bundle is None or dataset is None`
  or heatmap empty (L2143–2148, 2166–2178) — the veto is NOT universal.
- DeepCenter is a **pass/fail veto**, not a ranker (L2731–2732); surviving safe-division daughters
  are ordered by `parent_dist + 0.15*sister_dist` (L2740–2746).
- **TWO direct DeepCenter consumers, corrected (Codex v2 #2).** The heatmap veto is called at
  exactly two sites: **gap1** inside `close_single_frame_gaps` (acceptance call N cell2:2454) and
  **safe-division** (N cell2:2731). `recover_strict_gap2` (N cell2:2497–2632) has **no** detector
  argument, heatmap lookup, or DeepCenter acceptance call — it is NOT a direct consumer; it only
  runs downstream of gap1 (stage order gap1 → gap2 → safe-div, N cell2:3047–3052) and can change
  the graph *indirectly* after gap1's changed vetoes. So the heatmap enters at gap1, before gap2
  and safe-division. The pre-first-consumer snapshot boundary is therefore **before gap1**.

**Caches / resume (must all be handled):**
- Inner heatmap cache `heatmap_cache` keyed `(dataset,t)` (N cell2:2093).
- **Outer persistent heatmap wrapper** (N cell3:258–269, the exp_060 harness monkeypatch) also
  keyed `(dataset,t)`; it can return a cached heatmap **before** the inner function runs.
- `_postprocess_resume_signature` hashes selected **globals**, not arbitrary env vars (N
  cell2:318–325). Base/final **submission-resume records** (N cell2:3198–3203, 3814–3817) are the
  demonstrated resume hazard; adding a new env flag alone does NOT invalidate them.

**Z-exclusion evidence (correct anchor):**
`experiments/repro_003_public_0933_kaggle_slug/remote_output/tracking_repo/scripts/predict_unet_transformer.py`:381–384
excludes Z from the **detection** TTA as OOD. This is a detection-model comment; it does NOT
prove the DeepCenter checkpoint treats a Z reflection as OOD (a Z reflection preserves axial
spacing). Treat Z-symmetry as an **uncertain assumption**.

## 3. Falsifiable hypothesis, arms, decision rule

**Hypothesis (falsifiable):**
> Changing the DeepCenter TTA set (parent XY-only → `zon` with Z-reflection, or → `xyd4` with a
> uniform 8-view D4), all else frozen and the resolved PP config pinned, changes the accepted
> gap-repair/division veto outcomes enough to yield a Public LB score differing from 0.947 at
> displayed 3-dp precision.

**Pre-registered arms — EXECUTABLE forward/inverse transforms (Codex v2 #1).** Each view is
`Tᵢ⁻¹(model(Tᵢ(x)))`; accumulate left-to-right then divide by the executed-view count. All indices
are the last two spatial dims for XY, dim −3 for Z. Exact definitions (torch semantics):

| id | forward `T(x)` | inverse `T⁻¹(y)` | coordinate map (assert on asymmetric fixture) |
| --- | --- | --- | --- |
| `V0` | `x` | `y` | identity |
| `Vx` | `flip(x,(-1,))` | `flip(y,(-1,))` | X-flip |
| `Vy` | `flip(x,(-2,))` | `flip(y,(-2,))` | Y-flip |
| `Vxy` | `flip(x,(-2,-1))` | `flip(y,(-2,-1))` | XY-flip |
| `R1` | `rot90(x,1,(-2,-1))` | `rot90(y,-1,(-2,-1))` | 90° rot |
| `R3` | `rot90(x,3,(-2,-1))` | `rot90(y,-3,(-2,-1))` | 270° rot |
| `Td` | `transpose(x,-1,-2)` | `transpose(y,-1,-2)` | main-diagonal |
| `Ta` | `transpose(rot90(x,1,(-2,-1)),-1,-2)` i.e. `rot90(x,1,(-2,-1)).transpose(-1,-2)` | `rot90(transpose(y,-1,-2),-1,(-2,-1))` | **X-flip orientation** (parent, N cell2:2124–2126) |
| `Aad` | `flip(transpose(x,-1,-2),(-2,-1))` | `flip(transpose(y,-1,-2),(-2,-1))` (self-inverse) | anti-diagonal |
| `Z∘T` | `flip(T(x),(-3,))` | `T⁻¹(flip(y,(-3,)))` | axial reflect then T |

`Ta` and `Vx` share the X-flip **orientation** but are **distinct forwards** (distinct inputs) and
must both be executed and cached separately — no dedup. Fixture assertions check the **coordinate
mapping** (a nonzero marker at an asymmetric position lands where the map predicts), NOT merely
`T⁻¹(T(x))==x` (a wrong `T` paired with its own correct inverse would pass that weaker check).

| Arm | Ordered views (parent order preserved) | #forwards executed | Notes |
| --- | --- | --- | --- |
| `xyonly` | V0,Vx,Vy,Vxy,R1,R3,Td,**Ta** | **8** (7 orientations; Ta a distinct forward) | **exactly the parent**; Ta added once at its own slot (weight 1), NOT `2×Vx` |
| `zon` | the 8 above **+ Z∘each** | **16** | Z∘ applied to whichever XY views ran this frame |
| `xyd4` | V0,Vx,Vy,Vxy,R1,R3,Td,**Aad** (replaces Ta) | **8** | uniform D4, no duplicate, no Z |

Nonsquare-XY frames: the parent applies only the 3 flips (rot/transpose/anti-transpose skipped).
Same rule per arm; `zon` adds Z∘(the applied views); `xyd4`'s `Aad` requires square XY, else it
degenerates to the flip-only set (documented + tested). **Equal per-slot weight 1** for every
executed view in every arm; the mean divides by the executed-view count.

**Decision rule (Public LB, displayed 3-dp) — deliberately narrow, per-arm SELECTION only:**
- An arm **≥ 0.948** → that arm's TTA change improved the displayed LB; adopt it (separate
  authorized step); no unplanned neighbour probe under this authorization.
- **== 0.947** → "no displayed difference for this arm." Record; do not interpret as mechanism.
- **≤ 0.946** → that arm's TTA direction regressed on the displayed LB. Revert; retain repro_059.
- **Both experimental arms ≥ 0.948:** pre-registered tie preference = **adopt `xyd4`** (in-group,
  geometrically principled, no OOD-Z risk); `zon` logged as a secondary positive.

**Conclusions are limited to the two interventions**, e.g. "Z averaging regressed," "D4
reweighting improved," or "no displayed difference." OOD-Z is a *possible* explanation, never an
identified cause. No cross-arm claim ("representation layer is LB-insensitive") is licensed. No
train16 proxy selects anything; test-set division confusion is unmeasurable.

## 4. Exact change (the ONLY behavioral differences) + cache/resume contract

1. **Add a per-arm TTA spec** to `deepcenter_heatmap_for_frame` selected by a canonical **TTA
   signature** = `(ordered_transform_list, per-view_multiplicity, aggregation="mean", impl_version,
   checkpoint_sha, input_provenance)`. `xyonly`'s signature reproduces the parent block byte-for-
   byte in structure and accumulation order.
2. **View-level prediction cache (budget + isolation fix).** Cache each unique **view prediction**
   `model(Tᵢ x)` keyed by `(dataset,t,canonical_view_id,checkpoint_sha,input_provenance)` — NOT
   completed heatmaps. Each arm accumulates its own ordered view list (its own weights/order) from
   this shared, immutable, provenance-keyed store. This bounds forwards to the **union** of views
   across arms (§7), and shares only verified upstream predictions (never a completed heatmap
   across signatures).
3. **Per-arm isolated heatmap caches.** Give each arm a **fresh, isolated** heatmap-cache dict
   (inner) AND replace/parameterize the outer persistent wrapper (N cell3:258–269) so its key
   includes the TTA signature; a genuinely fresh dict per arm is sufficient without changing the
   inner key, but the outer wrapper MUST NOT serve another arm's heatmap. Negative tests for
   wrong-arm / missing-signature / stale-impl-version reuse.
4. **Resume-artifact contract.** Enumerate and invalidate every postprocessing-derived resume
   artifact keyed on config (base/final submission-resume records, N cell2:3198–3203, 3814–3817):
   bind them to the TTA signature and **reject** any legacy artifact lacking it (fail-closed), so
   no arm reuses another arm's (or the parent's) resume state. Do not claim heatmap-caching resume
   artifacts beyond those actually anchored in code.
5. **Replay boundary = before the first DeepCenter consumer (P1-1 fix).** Build a frozen graph
   snapshot immediately **before `close_single_frame_gaps`** (or replay full `filter_output_graph`
   from immutable raw predictions). Deep-copy nodes/edges/stats/bookkeeping; reset effective config
   per arm; preserve insertion/traversal order. Reusing the parent's post-gap graph is FORBIDDEN
   (it would suppress the gap-closing part of the treatment).
6. **Everything else frozen** at the parent's runtime-captured resolved config (adaptive PP-sweep
   DISABLED; `tight55`/`MOTION_RELINK_TIGHT_UM=5.5` and all resolved globals pinned;
   `DEEPCENTER_SAFE_DIV_THRESHOLD=0.20`, `DEEPCENTER_GAP_THRESHOLD=0.25`, checkpoints, ILP,
   edge/detection TTA switches unchanged). Recover the resolved config from repro_059's kernel
   OUTPUT (`ppsweep_selected.json` + resume record + submission SHA), exactly as exp_060.

## 5. Isolation, validity, and telemetry (Codex-aligned)

- **Freshly-computed byte-parity control + shared-view equivalence (P2-5 / Codex v2 #4).** `xyonly`
  must produce a `submission.csv` SHA256-identical to repro_059 (56313491) — computed FRESH this
  run through the **same cached accumulation path the experimental arms use** (a resumed parent CSV
  is NOT proof, and the original-function path alone does NOT validate the cached path `zon`/`xyd4`
  rely on). The cached path MUST preserve the parent's exact **left-to-right, out-of-place,
  same-dtype (lossless float32) accumulation** from immutable cached logits, with `Ta` added once
  at its own slot (never `2×Vx`); a stacked/tree reduction, reduced-precision cache, or in-place
  mutation is NOT assumed equivalent and is forbidden. Byte-parity additionally requires
  equivalence of input tensors, model eval state, precision, normalization, sigmoid, graph
  traversal, resolved config, and CSV serialization. **Fallback discipline:** if parity fails,
  STOP and diagnose; a predefined implementation fallback (e.g. reverting to the parent's inline
  per-view accumulation) must be applied **consistently across ALL THREE arms** and its shared-view
  numerical equivalence re-verified — never leave `xyonly` on one path and the experimental arms on
  another. (The unmodified-parent fallback costs the parent's **8 forwards/square frame**, plus
  replay.) Keep the remote SHA gate; do NOT require remote GPU parity as a prerequisite to the run
  that measures it.
- **Separate execution-validity from observed-response (P2-5).**
  - *Execution validity (per arm):* intended ordered transforms + inverses applied, view counts,
    finite logits/heatmaps, cache provenance/signature correct. Verified on an **asymmetric
    coordinate fixture** so a wrong transform/inverse cannot pass (P2-4).
  - *Observed response:* on a defined matched frame set, report `zon`/`xyd4` vs `xyonly`
    mean/max |Δlogit|, candidate-score shifts, **veto crossings at BOTH gap-repair and division
    gates**, and final fork/edge/node identity diffs. A verified **zero** observed response is a
    recorded mechanism NULL (and MUST prevent a duplicate/byte-identical LB submission), NOT an
    implementation failure. The old `delta==0.0` raise is removed.
- **Mechanism-active + downstream telemetry (unambiguous identities).** Instrument the **two
  direct DeepCenter veto call sites** — gap1 (N cell2:2454) and safe-division (N cell2:2731) — per
  arm, per candidate: dataset, frame, the relevant node IDs (endpoint IDs for gap1;
  parent/existing-child/candidate-child for division), DeepCenter score, bypass flag (missing
  model/data/score paths, N cell2:2166–2178), veto pass/fail, and final-graph survival by exact
  identity. Trace `recover_strict_gap2` separately as a **downstream graph change** (it reads no
  heatmap), not as a veto. Report Δ(final forks), Δ(final gap1 edges), Δ(final gap2 edges),
  Δ(final nodes) per arm.
- **Isolation checks (admission-verified):** arm-order invariance; shared view-prediction store is
  immutable across arms; no RNG dependence in replay stages; insertion/traversal order preserved
  (tied scores depend on it) — all via bounded local fixtures, not repeated full GPU replays.

## 6. Primary risk: is a Z-reflection appropriate? (reframed per P2-6)

- The DeepCenter model is a 3D center-prior UNet. Z-symmetry of its learned features is
  **unknown**: a Z reflection preserves axial spacing but the checkpoint may still be
  depth-asymmetric (training-augmentation history / depth-dependent signal). If it is, averaging a
  Z-flipped prediction into the heatmap degrades it and `zon` **regresses**.
- The detection-TTA Z-exclusion (repro_003 predict script L381–384) is *suggestive* but is a
  different model; it is not proof for DeepCenter.
- Handling: `xyonly` byte-parity keeps any effect causally isolated; `xyd4` is the
  **geometrically better-motivated** in-group companion (XY isotropy supports the symmetry, though
  this does not establish the training distribution); the pre-registered rule treats `zon` ≤0.946
  as a real regression bound and ==0.947 as unresolved. We do not pre-claim Z helps.

## 7. Budget, execution order, stop rule, rollback

- **Forward-pass budget (the P1-2 / Codex v2 #3 fix).** The parent executes **8 forwards/square
  frame** (not 7 — Ta is a distinct forward). With the view-level cache keyed
  `(dataset,t,view,checkpoint_sha,provenance)`, the DeepCenter forwards needed = the **union of
  distinct input transforms** across arms, computed once per frame and reused by every arm:
  - shared inputs (all arms): V0,Vx,Vy,Vxy,R1,R3,Td = **7**
  - `Ta` (xyonly + zon): **+1**
  - `Aad` (xyd4 only): **+1**
  - `Z∘{V0,Vx,Vy,Vxy,R1,R3,Td,Ta}` (zon only): **+8**
  - → **17 distinct forwards / square frame** across all three arms (vs a naïve 8+16+8=32; vs 8
    for the parent's single heatmap). Nonsquare frames use fewer. Divergent graphs may request
    different frames; the cache is per `(dataset,t,view)` so any overlap is still shared.
- **Resource worksheet (grounded, provisional — Codex v2 #3 / v3 #2,#3).** Anchored on the
  in-repo parent artifact `experiments/repro_059_public_0947_exact_copy/artifacts/ppsweep_results.csv`
  (the same figures were also observed in the exp_060 kernel output). All numbers are provisional
  and MUST be replaced by a build-time timing probe before the run is admitted; they are not
  evidence of feasibility.
  - *Scored-frame demand:* per-movie `deepcenter_gap_checked` + `deepcenter_safe_div_checked` are
    O(10²) each (e.g. 44b6_0b24 ≈ 233 gap + 232 safe-div); distinct heatmap **frames** are fewer
    (many candidates share a `t`). The build-time probe MUST measure the distinct-frame count and
    the per-forward ms.
  - *Shared inference:* the edge/detection pipeline is unchanged (`predict_minutes_total` ≈ 10.4
    min for raw prediction); the full repro_059 run was ≈1.17 GPU-h — the balance is DeepCenter
    heatmaps + ILP + postprocessing.
  - *Adaptive PP-sweep — disabled outright (v3 #2 / admission #6).* The build injects a strippable
    `os.environ['BIOHUB_VALIDATOR_ENABLE'] = '0'  # exp061` at the top of the parent cell (before the
    parent reads it at `VALIDATOR_ENABLE = os.environ.get('BIOHUB_VALIDATOR_ENABLE','1')`). This
    turns off the **entire validator + adaptive PP-sweep** (both `selected_label='base'` and
    `selected_config={}` are unconditional defaults, so the parent path stays valid). The xyonly
    replay pins `tight55` itself, so the sweep is pure overhead here and is safely removed — the
    gate REQUIRES `validator_sweep_disabled`. `ppsweep_results.csv` shows the sweep is **8 rows,
    390.835–413.262 s each, 54.5265 min** (base + 7 candidates; 7 non-base = 47.6832 min) on 8
    validation samples WITH scoring — so disabling it reclaims roughly that, the largest single
    reason exp_060 hit 2.0 h. This is still a **historical-timing** figure; final feasibility is the
    build-time probe's call, but with the sweep off, 3 arms are expected to fit comfortably.
  - *Replays:* three CPU `filter_output_graph` replays from the pre-gap1 snapshot on the **4 test
    movies**. The 390.835–413.262 s/row figures above are **validation-sample + scoring** timings
    and do NOT directly give the test replay cost — the probe must measure the test replay
    separately.
  - *Cache placement / capacity (v3 #3).* Because arms run **sequentially** (`xyonly` completes all
    frames before `zon` starts), view predictions MUST persist across the whole run. Policy:
    **lossless disk-backed** per-`(dataset,t,view)` logit store (float32), written once on first
    request by any arm and **retained until all arms finish**, with a **bounded RAM LRU** in front;
    GPU tensors freed immediately after each forward. Budget the disk store as
    `#distinct_frames × #views(≤17) × logit_tensor_bytes` and include read/write I/O in the
    admission estimate. (The earlier "stream + evict per frame" idea is **removed** — it is
    incompatible with sequential arm execution and divergent per-arm frame demand.)
  - **Provisional estimate ≈ 1.4–1.8 GPU-h; reserve 2.0 GPU-h; hard 2.0-h watchdog** — provisional
    until the build-time probe supplies measured frame count, per-forward ms, test replay cost,
    and disk I/O.
- **Protected execution order + partial-run safety (P1-2).** Run **`xyonly` → `zon` → `xyd4`**
  (parity control first, then the declared primary, then the companion). After each arm: write its
  `submission.csv` + telemetry as an **atomic completed-arm artifact**; record explicit partial-run
  status in `metrics.json`. **Numeric finalization reserve = 20 min**: do NOT start an arm unless
  `remaining_budget ≥ measured_arm_cost + 20 min`. A watchdog is a spending bound, not proof all
  arms fit; if `xyd4` cannot start with margin, finish cleanly with xyonly+zon and report `xyd4`
  as not-run (a valid partial result, unlike exp_060's mid-arm kill). Arm admission is gated by the
  MEASURED running rate, not the provisional estimate.
- **Stop rule:** stop on `xyonly` fresh-control SHA mismatch, non-finite logits/heatmaps, config
  drift, any cross-arm cache/resume leakage, or the 2.0-h reservation. No auto-retry.
- **Rollback:** all additions are env/signature-gated and purely additive; with the flag off the
  notebook is prediction-equivalent to repro_059. Retain repro_059 as parent unless an arm ≥0.948.
- **If the 3-arm design cannot credibly fit** the measured budget at build time, return the
  budget/scope conflict to the user for direction BEFORE launch (drop to xyonly+one experimental
  arm, or split into two runs) rather than risk a mid-arm watchdog kill.

## 8. Arm set — RESOLVED (user, 2026-09-20)

Option (ii): build all three arms in one run: `xyonly` (byte-parity control) + `zon`
(Z-reflection, primary) + `xyd4` (XY-D4 repair, companion). Most informative; the view-cache +
protected order + partial-run safety of §7 make it **feasible CONDITIONAL on the measured §7
build-time admission estimate** (not asserted feasible in advance) — if the probe shows 3 arms
cannot fit with the 20-min reserve, drop to xyonly + one experimental arm or split into two runs.

## 9. LB submission route per arm (the P2-8 fix)

The competition is **notebook-only (code submission)**: the LB scores the notebook's OUTPUT
`submission.csv`. One run yields three CSVs, but only the notebook's canonical `submission.csv` is
scored. Per exp_060's proven route, each experimental arm is submitted via a **separate arm-
promotion notebook** whose OUTPUT `submission.csv` IS that arm — either (a) a variant re-run with
an env flag promoting `zon`/`xyd4` to `SUBMISSION_PATH` (as `safediv018-lb-submit` did for the
0.18 arm; ~1 GPU-h each), or (b) if precomputed-CSV serving is confirmed legal, a trivial CPU
notebook copying the arm CSV — legality to be verified first. Each submission: exact SHA
verification vs the run's arm CSV, gate via `scripts/gate_submission.py`, record in
`SUBMISSION_BUDGET.json` with authenticated `score_source`. **Never resubmit byte-identical
outputs.** Two experimental arms ⇒ up to two LB reads, each a SEPARATE user authorization.

## 10. Governance / next gates

Not authorized to implement or launch. Sequence: this v2 → Codex re-challenge (to CONSENSUS) →
build on the repro_059 snapshot with `admission.require_codex_review: true` → fresh Codex admission
PASS → local behavior test (asymmetric-fixture transforms, cache/resume negative tests, arm-order
invariance, config-diff) + snapshot smoke → 2.0-h reservation → ONE user-authorized launch → per-
arm LB submission(s) vs 0.947 (each separately authorized) → record + interpret → **then fire the
ARMED `pending_followup` reminder for option B.** Claude never plays the Codex reviewer role.

## 11. Risks summary

| Risk | Handling |
| --- | --- |
| Replay reuses post-gap graph → suppresses treatment | §4.5: snapshot BEFORE `close_single_frame_gaps`; gap-veto telemetry |
| 3 arms overrun the watchdog (thr022 repeat) | §7: view-cache (17 distinct fwd/frame union), order xyonly→zon→xyd4, per-arm atomic artifacts, 20-min finalization reserve, don't-start-without-margin, partial-run status, runtime-gated admission |
| Cache/resume leakage across arms | §4.2–4.4: view-level provenance cache, per-arm isolated heatmap caches, signature-bound resume rejection, negative tests |
| `xyd4` computed as 9 views keeping the duplicate | §3: `xyd4` REPLACES Ta with Aad; asymmetric-fixture transform/inverse test |
| Valid null misread as impl failure | §5: execution-validity ≠ observed-response; verified zero = mechanism null (blocks dup submit) |
| Byte-parity broken by refactor | §5: FRESH control SHA vs repro_059 via the SAME cached path the experimental arms use; on failure STOP & diagnose, or apply the SAME fallback across ALL arms + re-verify shared-view equivalence (never xyonly-only) |
| Over-claiming mechanism/OOD | §0,§1,§3,§6: veto not ranker; Z = uncertain assumption; conclusions limited to the two interventions |
| Z-reflection OOD → `zon` regresses | §3/§6: pre-registered ≤0.946 regression bound; `xyd4` companion isolates it |
| Submission route unproven | §9: per-arm promotion notebook (exp_060-proven), SHA-verify, no byte-identical resubmit |
| Below LB display grain (as exp_060) | §1/§3: null is a valid recorded outcome; no claim it must exceed exp_060 |

## 14. Codex challenge v1 (REVISE) — resolution table

| # | Codex v1 finding | Resolution in v2 |
| --- | --- | --- |
| P1-1 | Replay boundary before gap-closing, not safe-div | §2 consumer order; §4.5 snapshot before `close_single_frame_gaps`; §5 gap-veto telemetry |
| P1-2 | 3-arm budget unsupported; watchdog-kill risk | §7 view-cache union (17 distinct fwd/frame) + component budget + order xyonly→zon→xyd4 + 20-min finalization reserve + atomic per-arm artifacts + partial-run status + don't-start-without-margin + return-scope-conflict clause |
| P1-3 | Inner-key fix insufficient; cache+resume leakage | §2 cache/resume anchors; §4.2 view-level provenance cache; §4.3 per-arm isolated + outer-wrapper signature; §4.4 signature-bound resume rejection + negative tests |
| P2-4 | `xyd4` under-specified; "in-distribution" unproven | §3 exact ordered transforms/inverses/weights, xyd4 REPLACES Ta with Aad, nonsquare rule, asymmetric-fixture test; "geometrically better motivated" wording |
| P2-5 | Guard conflates null with failure; control SHA | §5 execution-validity vs observed-response; verified zero = mechanism null; FRESH control SHA + fallback |
| P2-6 | Scientific overclaim; veto not ranker; Z anchor | §0/§1/§2/§6 veto (L2731–2746); correct Z-comment anchor (repro_003); Z = uncertain assumption; removed "must exceed" + "+11 below LB" claims |
| P2-7 | Interpretation matrix overclaims; incomplete rule | §3 conclusions limited to the two interventions; both-improve tie preference = adopt xyd4; no unplanned neighbour probe |
| P2-8 | 3 CSVs → 2 LB reads route missing | §9 per-arm promotion notebook route, SHA-verify, no byte-identical resubmit, each separately authorized |
| NB | universal-gating overstatement; byte vs prediction; stale arm language | §2 veto bypass (L2166–2178); §7 "prediction-equivalent"; §8 arm set resolved |

## 15. Codex challenge v2 (REVISE, narrowed) — resolution table

v2 confirmed P1-1, P1-3, P2-6, P2-7, P2-8 resolved. Remaining items fixed in v3:

| # | Codex v2 finding | Resolution in v3 |
| --- | --- | --- |
| v2-1 (P2) | Transform spec contradicts parent (`Ta` composition; weaker inverse test) | §3 executable forward/inverse table: `Ta(x)=transpose(rot90(x,1))` ≡ X-flip, inv `rot90(transpose(y),-1)`; `Aad(x)=flip(transpose(x),(-2,-1))` self-inverse; explicit Z inverses; equal per-slot weight 1; fixture asserts **coordinate mappings**, not just `T⁻¹(T(x))==x` |
| v2-2 (P2) | gap2 invented as a DeepCenter consumer | §2 + §5: TWO direct consumers only — gap1 (N cell2:2454) + safe-div (N cell2:2731); `recover_strict_gap2` (2497–2632) reads no heatmap → traced as a downstream graph change, not a veto; snapshot before gap1 |
| v2-3 (P1) | Timing/cache-capacity unsupported; parent does 8 forwards not 7 | §7: parent = **8 forwards**, union = **17 distinct forwards/frame**; grounded resource worksheet; numeric **20-min finalization reserve**; build-time timing probe measures frame count + per-forward ms; estimate labeled provisional. *(NOTE: this row's original "≈60-min sweep removal" and "eviction/stream policy" wording is **SUPERSEDED by v4 §7** — only the 7 candidate passes (47.6832 min historical validation-with-scoring, base pass retained) are removed as a bounded/must-be-measured saving, and the cache is a disk-backed store retained until all arms finish. See §16 rows v3-2/v3-3.)* |
| v2-4 (P2) | Parity fallback can hide a cached-path discrepancy | §5: xyonly parity computed through the **same cached path** the experimental arms use; exact left-to-right out-of-place lossless-float32 accumulation, `Ta` once (not 2×Vx); on failure STOP & diagnose or apply the SAME fallback across ALL arms + re-verify shared-view equivalence; fallback cost = 8 forwards/frame |
| v2-5 (P3) | Active STATE.json exp061 fields retain withdrawn claims | STATE.json exp061 reconciled to v3 assumptions (Z = uncertain symmetry assumption; xyd4 = geometrically better-motivated, REPLACES the duplicate; conditional feasibility); historical challenge records unchanged |

## 16. Codex challenge v3 (REVISE, cleanup-only) — resolution table

v3 confirmed the corrected transforms and reopened nothing. Five consistency/accounting fixes in v4:

| # | Codex v3 finding | Resolution in v4 |
| --- | --- | --- |
| v3-1 (P2) | §0/§1 still said "three consumers" / "two gap-repair vetoes" | §0/§1 corrected to TWO direct consumers (gap1 L2454 + safe-div L2731); gap2 downstream |
| v3-2 (P1) | Sweep-saving over-claimed; validation-scoring vs test-replay conflated; artifact ref inaccessible | §7: only the **7 candidate passes** removed (base pass retained); sweep rows are 8 validation samples WITH scoring, NOT a 4-movie test replay; removed the unconditional "more-than-offsets"/feasibility claim; artifact ref → in-repo `experiments/repro_059_.../artifacts/ppsweep_results.csv` |
| v3-3 (P1) | "Evict per frame" incompatible with sequential arms; no capacity bound | §7: lossless **disk-backed** per-`(dataset,t,view)` store retained until all arms finish + bounded RAM LRU; budget `#frames×#views×bytes` + I/O; removed the frame-streaming alternative |
| v3-4 (P2) | Risk table still routed fallback to unmodified parent for xyonly (the loophole) | §5 + risk table: STOP or SAME cross-arm fallback with re-verified shared-view equivalence; never xyonly-only |
| v3-5 (P3) | STATE `v2_key_fixes` still asserted "~15 union … making 3 arms fit"; proposal risk table "~15 fwd" | STATE `v2_key_fixes` marked SUPERSEDED (17 forwards, conditional feasibility); proposal tables use 17 |

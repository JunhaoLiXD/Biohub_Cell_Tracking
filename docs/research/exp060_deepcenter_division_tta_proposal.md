# exp_060 — DeepCenter safe-division threshold micro-sweep

Record type: versioned strategy proposal.
Status: **v3 — CONSENSUS (Codex gpt-6-astra, 2026-09-18, after REVISE v1+v2).** Strategy is
agreed; see §13. Implementation is NOT yet authorized — it still requires a fresh Codex
*admission* PASS + local test + snapshot smoke + budget reservation before any launch. No
leaderboard submission is authorized by this document.
Author: Claude Code. Date: 2026-09-18.
Parent: **repro_059_public_0947_exact_copy** (Public LB **0.947**, authenticated submission
56313491). Evidence: `experiments/repro_059_public_0947_exact_copy/PROVENANCE.md`, `STATE.json`.
Challenge history: `exp060_codex_challenge_v1.md` (REVISE; pivot to threshold sweep),
`exp060_codex_challenge_v2.md` (REVISE, converging — core code claims verified).

> **Revision trail.** v1 = strengthen DeepCenter TTA via a Z-axis reflection. Codex v1 REVISE:
> a threshold micro-sweep is a better-isolated, cheaper first probe, and v1's TTA-group
> description was wrong. v2 pivoted to the threshold sweep; Codex v2 verified the core claims
> and left 3 narrow items + wording fixes. v3 folds those in (see §12). The corrected
> Z-reflection TTA is deferred to **exp_061** (§9).

---

## 0. One-paragraph summary

The 0.947 parent accepts a candidate `safe_division` only if the DeepCenter heatmap score at
the daughter point clears `DEEPCENTER_SAFE_DIV_THRESHOLD = 0.20`. That threshold is a single
knob, *separate* from the gap veto threshold (`DEEPCENTER_GAP_THRESHOLD = 0.25`), and it does
not change the heatmap (so all arms share byte-identical cached heatmaps). This experiment runs
**one Kaggle inference**, then per arm RE-RUNS the full `filter_output_graph` from a freshly
reloaded graph per movie (stronger isolation than deep-copy; the DeepCenter heatmaps are shared
across arms so there is no GPU re-inference, but the CPU pre-safe-division stages ARE recomputed
per arm) at three thresholds — **0.20 (byte-parity control), 0.18, 0.22**
— with the parent's *runtime-captured* resolved post-processing configuration pinned (adaptive
PP-sweep disabled). It produces three `submission.csv` files and submits the **two changed arms**
(0.20 is byte-identical to repro_059, so it is not resubmitted) to the now-unlimited Public LB.
It is the cheapest, best-isolated test of whether the division gate is an LB-movable lever.

## 1. Motivation

- **Division is the bottleneck with the most headroom** (A0 Part 1: edge layer ~LB-flat).
  Two causally-isolated edge/motion edits (exp_055, exp_057) were LB-flat.
- **The safe-div threshold is the most isolated division knob.** `DEEPCENTER_SAFE_DIV_THRESHOLD`
  gates *only* `safe_division` acceptance; gap-close uses the separate `DEEPCENTER_GAP_THRESHOLD`.
  Lowering the threshold (0.18) lets more borderline daughters **pass the score gate**; raising
  it (0.22) fewer. NOTE: passing the gate is not the same as a surviving final division —
  frame/global caps, conflicts, geometry, short-track filtering and smoothing all act
  downstream, and changed forks can in turn alter final nodes and even non-division edges. The
  intervention is division-exclusive; its downstream cascade is not.
- **Cheap and clean under the new submission policy.** Heatmap is threshold-invariant → three
  arms reuse one inference + cached heatmaps; unlimited LB submissions read the held-out answer.
- **It gates exp_061.** If directly changing the division threshold cannot move the LB, a
  heatmap-perturbing TTA (which only nudges scores *around* this same gate) is unlikely to —
  so this probe informs whether exp_061 (Z-TTA) is worth running (Codex null-mechanism).

## 2. Falsifiable hypothesis and decision rule

> The DeepCenter safe-division accept threshold (parent 0.20) is an LB-movable division lever:
> at least one pre-registered arm in **{0.18, 0.22}**, all other parent behavior frozen and the
> resolved PP config pinned, yields a Public LB score differing from 0.947 at displayed precision.

**Pre-registered arms (fixed before any submission):** 0.20 control, 0.18, 0.22. Do **not**
widen the bracket after seeing results; a post-hoc wider sweep is exploratory tuning, labeled
as such, not generalization evidence.

**Decision rule (Public LB, displayed 3-dp) — deliberately narrow:**
- Any arm **≥ 0.948** → this threshold moved the LB; adopt it as the new parent (adoption is a
  separate authorized step). One neighbor may then be probed as *exploratory tuning*.
- Both arms **== 0.947** → the effect of *this bracket* is **unresolved below displayed
  precision**. This does NOT close threshold tuning and does NOT rule out TTA; it only says
  {0.18,0.22} produced no displayed movement. Record the null; decide next lever separately.
- Any arm **≤ 0.946** (none ≥ 0.948) → this direction regressed on the LB *in this bracket*.
  This does NOT prove 0.20 is optimal. Retain repro_059; do not over-interpret.
- A tie at 0.947 is reported as unresolved below precision, never "divisions unchanged".

## 3. Exact change (the ONLY behavioral difference)

- The single swept variable is `BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD` ∈ {0.20, 0.18, 0.22}.
- **Everything else is frozen at the parent's runtime-captured resolved values.** The adaptive
  PP-sweep is **DISABLED**; the effective post-processing configuration is not reconstructed
  from a label but **captured from the parent run's artifacts** — its recorded base config plus
  the sweep's *selected overrides* (the resolved `PP_SWEEP_KEYS` values repro_059 actually used,
  including `tight55`=MOTION_RELINK_TIGHT_UM 5.5) — and pinned as explicit effective globals for
  every arm. No arm re-derives or re-selects any of it.
- All TTA switches, `DEEPCENTER_GAP_THRESHOLD=0.25`, checkpoints, weights, ILP settings, and
  every other post-processing parameter are unchanged. Heatmap generation is unchanged, so
  `(dataset,t)` heatmap caching is correct and shared across arms.

## 4. Isolation discipline (Codex-aligned)

- **Division-exclusive intervention.** Only the safe-div gate threshold changes; the gap veto
  (separate threshold) is untouched. (Downstream cascade may still touch non-division
  nodes/edges via short-track/smoothing — this is measured, not assumed away; see telemetry.)
- **Pinned, runtime-captured PP config.** Every arm (incl. the 0.20 control) uses the identical
  pinned effective config captured from parent artifacts; the adaptive sweep does not run.
- **Byte-parity control.** The 0.20 arm must produce a `submission.csv` **SHA256-identical to
  repro_059's** (submission 56313491). If not identical, the pinned config / replay path
  diverged → the run is invalid and stops before any 0.18/0.22 result is trusted.
- **Attribution telemetry (unambiguous identities).** Per arm, per candidate, record: dataset,
  frame, **parent node ID, existing-child node ID, candidate-child node ID**, DeepCenter score,
  missing/nonfinite **bypass** flag, gate pass/fail, and whether the fork **survives all
  downstream stages** into the final graph — tracked by **exact final fork and edge identities**
  (daughter position alone cannot distinguish competing parents). Report Δ(final surviving
  forks), Δ(final edges), Δ(final nodes) between arms. Counts of gate passage alone cannot
  attribute an LB delta.

## 5. Validation protocol

1. **Local (zero-GPU) config-diff test:** for each arm, assert the ONLY effective difference vs
   the pinned parent config is `DEEPCENTER_SAFE_DIV_THRESHOLD`; assert the adaptive sweep is
   disabled and the pinned effective globals equal the parent's runtime-captured selection.
2. **One Kaggle run — explicit replay design (Codex fix #1).** Run test inference once. Build a
   **frozen pre-safe-division graph** (the pipeline state immediately before `add_safe_divisions
   _postlink`) and an **independent deep copy per arm** so `filter_output_graph`'s fresh caches
   and in-place edits cannot cross-contaminate arms. **Retain** the DeepCenter heatmaps/scores
   for the needed frames (raise the `_dc_cache_trim` / `DEEPCENTER_SCORE_CACHE_MAX_FRAMES` limit
   or pre-materialize them) so no arm re-infers. Give each arm its **own output path and resume
   record** so `write_test_submission` does not overwrite a single shared CSV. Emit three
   `submission.csv` + the §4 telemetry. Verify the 0.20 output is SHA-identical to repro_059
   before trusting the others.
3. **Public LB:** submit 0.18 and 0.22 (the 0.20 control is byte-identical → not resubmitted).
   Record each in SUBMISSION_BUDGET.json with authenticated `score_source`; apply §2.

No train16 proxy decides anything. The parent's own test-set division confusion is **unmeasured
and unmeasurable** (test ground truth is unavailable); telemetry emits predicted fork
identities/counts only. Any division *confusion* would require labeled training movies and is a
separately-scoped exploratory baseline, out of this experiment's prediction-preserving scope.

## 6. Expected signal, failure modes

- **Expected:** small effect in one direction if the gate sits near a decision cliff; plausibly
  null if 0.20 is on a flat part of the division precision/recall trade.
- **Null (both 0.947):** the *bracket* {0.18,0.22} shows no displayed LB movement — a valid,
  informative bound (does not close tuning, does not rule out TTA).
- **Regression (≤0.946):** this bracket regressed; revert; do not claim optimality or mechanism.
- **Invalid run:** 0.20 control not SHA-identical to repro_059 ⇒ replay/pin bug ⇒ stop, no submit.

## 7. Budget, stop rule, rollback

- **Cost model (estimate, not measured):** ONE full test inference (~1.17–1.3 GPU-h dominant),
  the parent's own adaptive PP-sweep + final submission (part of the byte-frozen parent run), then
  three per-arm FULL `filter_output_graph` re-runs (CPU pre-safe-div stages recomputed per arm;
  DeepCenter heatmaps shared across arms so no GPU re-inference). **Estimated ≈ 1.3–1.6 GPU-h** —
  an estimate to be confirmed at runtime, not evidence; enforced by the 2.0-h watchdog.
- **Budget:** reserve **2.0 GPU-h**; **hard stop at 2.0 h**; preserve six protected hours and
  ≥10% weekly model allowance. One launch only.
- **Stop rule:** stop on 0.20-parity mismatch, non-finite scores, config drift, or the 2.0-h
  reservation. No auto-retry on timeout/quota.
- **Rollback:** thresholds are pure config; revert to 0.20 ⇒ exact repro_059. Retain repro_059
  as parent unless an arm ≥ 0.948.
- **Governance:** unlimited LB submission count does NOT authorize execution; still requires
  CONSENSUS → fresh Codex admission PASS → local test + snapshot smoke → 2.0-h reservation →
  one launch. Adoption as parent is a separate step.

## 8. Governance / next gates

Not authorized to implement or launch. Sequence: this v3 → Codex re-challenge (to CONSENSUS) →
build on the repro_059 snapshot with `admission.require_codex_review: true` → fresh Codex
admission PASS → local config-diff test + snapshot smoke → 2.0-h reservation → ONE launch → LB
submissions → record + interpret → decide exp_061.

## 9. Deferred successor — exp_061: corrected Z-reflection DeepCenter TTA

Queued behind exp_060; run only if §2 shows the division gate is LB-movable (or as an
independent representation probe). Corrections carried from Codex v1:
- Parent DeepCenter TTA is **8 evaluations / 7 unique XY transforms** (`rot90(t,1).transpose`
  duplicates the X flip; anti-diagonal reflection missing), never touching Z. Adding a
  Z-reflection yields **16 evaluations / 14 unique**. (Repairing the XY group to a true
  8-unique-view D4 is a *separate* intervention.)
- A TTA change alters the **shared** heatmap consumed by BOTH safe-division AND gap-close, so
  exp_061 must use **separate heatmap caches per arm** (the `(dataset,t)` key is insufficient
  when the augmentation set differs) + invalidate resume artifacts, and replace the `delta==0`
  (augmented-vs-unaugmented) guard with a **Z-on vs XY-only** comparison, treating a genuinely
  unchanged output as a valid NULL, not an implementation failure.

## 10. Codex REVISE v1 — resolutions

| # | Codex v1 finding | Resolution |
| --- | --- | --- |
| 1 | "8-view D4" wrong (8 eval/7 unique, no Z) | Corrected; moved to exp_061 §9; XY-repair separated |
| 2 | Freeze RESOLVED pp config, not sweep code | §3/§4: adaptive sweep DISABLED, parent's runtime-captured resolved config pinned; 0.20 byte-parity |
| 3 | Counts ≠ surviving divisions; bypasses | §4: telemetry records candidate identities/score/bypass AND final surviving fork/edge identities |
| 4 | Cache key + delta guard | N/A for threshold sweep (heatmap invariant); carried into exp_061 §9 |
| 5 | Budget/stop reconciliation | §7: 1 inference + 3 replays, ≈1.3–1.5h ESTIMATE, reserve 2.0h, hard stop 2.0h |
| 6 | Narrow conclusions | §2/§5/§6: ties = unresolved below precision; repro_059 division baseline unmeasured; LB selection = tuning |

## 11. Codex REVISE v2 — resolutions

| # | Codex v2 finding | Resolution |
| --- | --- | --- |
| 1 | Specify replay implementation | §5.2: frozen pre-safe-division graph, per-arm deep copies, retained heatmaps (no `_dc_cache_trim` eviction), per-arm output/resume records; 1.3–1.5h labeled ESTIMATE |
| 2 | Narrow decision rules further | §2: ties/regression bounded to *this bracket*; neither closes tuning nor rules out TTA |
| 3 | Unambiguous telemetry identities | §4: dataset/parent ID/existing-child ID/candidate-child ID/frame/score + final fork+edge identities |
| §11.1 | Keep 0.18/0.22, don't widen | §2: pre-registered, no post-hoc widening |
| §11.2 | Capture parent runtime artifacts | §3: effective config captured from parent artifacts, not a reconstructed label; SHA parity retained |
| §11.3 | No test division confusion | §5: predicted fork identities/counts only; training-movie confusion out of scope |
| facts | division-exclusive intervention only; gate≠final; §0/§5 submission count | §1/§4 wording fixed; §0 = 3 files, 2 submissions |

## 13. CONSENSUS record + implementation notes (Codex v3, 2026-09-18)

**Verdict: CONSENSUS.** v3 resolves the remaining v2 items at the strategy level.
Implementation still requires a fresh admission PASS and the stated parity/smoke/budget gates.
Rulings on §12, to be honored by the builder:

1. **Resolved-config source (§12.1).** Neither `_guard_report` nor `CONFIG_DISPLAY` is
   authoritative — `CONFIG_DISPLAY` holds *initialization* values, and the sweep temporarily
   applies overrides then calls `pp_restore` before `_guard_report` reads globals. **Use the
   recorded base config PLUS `ppsweep_selected.json`'s explicit overrides, cross-checked against
   the final-submission resume record and SHA.** No sweep rerun is needed IF those parent
   artifacts fully establish the config. If they cannot be recovered, **rerun the unchanged
   parent sweep once**, emit the canonical effective dict *before* restoration, verify parent
   SHA parity, then freeze — and count that work in the budget. (⇒ first build step: recover
   `ppsweep_selected.json` + the resume record from the repro_059 kernel OUTPUT.)
2. **Arm isolation (§12.2).** Per-arm *process* isolation is unnecessary. Sufficient: a frozen
   pre-safe-division graph per dataset; deep-copied nodes/edges/**stats**; immutable retained
   heatmaps; explicitly reset config per arm; separate output/resume records. No RNG dependency
   in the replay stages. **Preserve insertion/traversal order** (tied proposal scores depend on
   it). Admission must verify **arm-order invariance** and that shared graph/heatmap inputs are
   unchanged across arms.
3. **Non-blocking wording:** §1 slightly overstates the threshold as "gating" while it also
   feeds gap repair downstream; the narrower §2 decision rules govern. Public-LB selection
   remains tuning evidence, not generalization proof.

## 12. Open questions for Codex (v3) — RESOLVED in §13

1. Is capturing the effective PP config "from parent artifacts" satisfiable given repro_059 was
   an external submission whose in-run resolved dict we hold only via the notebook's
   `_guard_report` / `CONFIG_DISPLAY` — is that the authoritative source, or must the successor
   re-run the parent's own sweep once to emit a canonical resolved dict before freezing it?
2. Is a single frozen pre-safe-division graph + per-arm deep copies definitely sufficient
   isolation, or are there earlier shared-mutable-state hazards (global caches, RNG) between arms
   that require full per-arm process isolation instead?

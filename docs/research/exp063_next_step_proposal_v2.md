# exp_063 next-step strategy — proposal v2 (Claude Code, after Codex challenge round 1)

Status: **PROPOSAL, revised after Codex `VERDICT: REVISE`.** No experiment, launch or submission is
authorized. Parent remains `repro_059` = Public LB **0.947** (submission 56313491).
Supersedes `exp063_next_step_proposal_v1.md`, which lists its own known-wrong claims below.

Date: 2026-09-24. Deadline **2026-09-29 23:59**. Codex challenge: `exp063_codex_challenge_v1.md`.

---

## 0. What v1 got wrong (Codex was right on all five)

| v1 claim | status | correction |
|---|---|---|
| 35.7 % line overlap ⇒ "a pipeline ~64 % different" | **overreach** | Text overlap measures neither execution nor behaviour. Correct finding: **exact-base portability was never established by the recon — and incompatibility is not established by me either.** |
| "PPSWEEP dropped ⇒ they lose our tight55" | **FALSE, and I verified it** | See §1. They hardcode `BIOHUB_MOTION_RELINK_TIGHT_UM = "5.5"` — the sweep's *selected value*, identical to ours. Codex predicted exactly this ("could freeze the selected parameters directly"). Marker counts proved nothing. |
| "0 for 4" on porting | **inflated** | exp_061 **never scored** — a transport failure, `UNRESOLVED, not falsified`. The measured record is **0 for 3** (exp_055, exp_057, exp_060). And repro_059 is a single event, not a base rate for "copying a public notebook". |
| "16.9 h free" | **wrong** | `reserve_hours` is **6.0** and protected. Discretionary GPU is **18.671187 − 1.75 − 6.0 = 10.921187 h**. |
| "5× more probes per hour" from their 19 min | **unverified** | A notebook *title* against our full-kernel 1.727 h is not a matched comparison. Treat runtime as unknown until measured. |

Codex's decision-rule objection is also accepted: arm A scoring ≤ 0.946 would show only that *our
frozen reproduction under our execution conditions* underperformed. It would **not** falsify the
author's mechanisms nor prove the 0.951 claim false. Equality at 0.947 would **not** prove
"relabelling" — rounded aggregate equality is not prediction equality.

---

## 1. The finding that reframes the whole question

Inspecting `haideptry/biohub-0-951-sota-deepcenter-fast-ilp-19m` directly (not the recon's summary),
its environment block **stacks four mechanisms at once on our own operating point**:

```
BIOHUB_MOTION_RELINK_TIGHT_UM = "5.5"     <- OUR tight55, frozen, not re-swept
BIOHUB_GAP_DENSITY_ADAPTIVE   = "1"       <- continuous density adaptation
BIOHUB_GAP_DENSITY_REFERENCE_UM = "6.5"   ;  GAIN = 0.040
BIOHUB_GAP_DENSITY_MAX_STEP_DELTA_UM = "0.125" ; NEIGHBORS = 3
BIOHUB_DIVNET_VERIFY = "1"  ;  BIOHUB_DIV_MIN_PROB = "0.50"
_lb_mutual = _lb_col_best & _lb_row_best   ;  raw = raw + _lb_rank_bonus
SAFE_DIV_REQUIRE_MUTUAL_NN                 <- a fifth, division-side gate
BIOHUB_PPSWEEP_SELECT_MARGIN = "0.001" ; BIOHUB_PPSWEEP_MAX_ADJ_LOSS = "0.0005"
```

Three consequences:

1. **It is our operating point plus a stack, not a different base.** It keeps `tight55 = 5.5`. The
   sweep *machinery* is reduced, but its *selected policy* is preserved. My v1 risk #4 is defused.
2. **exp_062's mutual-best patch is a strict subset of this notebook.** Whatever k2 returns is
   evidence about one of four stacked mechanisms — so a k2 null does **not** condemn this notebook.
3. **The recon's "Lever 2" description does not match this notebook.** The recon describes discrete
   low/middle/high groups with a `tight_um`/`relaxed_um`/`velocity_weight`/`learned_bonus` table;
   this notebook implements a *continuous* gap-density adaptation with a gain and a step cap. The
   recon's lever descriptions are **notebook-specific and not interchangeable** — a second reason
   not to treat "port lever 2" as a well-defined task.

This is the strongest available argument for the reproduction route, and it is mechanical rather
than base-rate: **testing the stack as shipped is the only way to evaluate the stack**, and
hand-porting four interacting mechanisms one at a time cannot be done in five days.

## 2. Revised proposal

`exp_063_public_pipeline_repro` — **one bounded reproduction**, verbatim, zero code authored by us.

**Arm A only, for now:** `haideptry/biohub-0-951-sota-deepcenter-fast-ilp-19m`.
Arm B (`biohub-sota-0-948-density-adaptive-2xt4-22m`) is **not** pre-approved; it requires its own
decision after A, and at most one further run.

**Comparator is `max(0.947, exp_062 k2)`**, not the stale 0.947 — per Codex, if k2 scores 0.949 then
A at 0.948 is a regression, not a gain.

### Minimum audit before any launch (Codex's list, accepted in full)

"We authored nothing" is not a safety argument — we inherit every upstream defect, and this project
has already been bitten by inherited cache and telemetry hazards. Required, and all zero-GPU:

- frozen notebook hash + acquisition metadata, archived **in-repo** (the combined notebook already
  went 403 on us; a pulled copy must not be allowed to evaporate)
- mounted dataset versions and the three checkpoint hashes pinned and matched against our parent's
- provenance of the added `giorgosi/biohub-divnet-v2` weights — accessibility is not permitted
  training provenance
- executed prediction path: cache/fallback behaviour, any GT read, any specimen-specific branch
- output schema + graph integrity + hidden-rerun compatibility, and **measured** runtime

Patch-parity and anchor-uniqueness tests are genuinely unnecessary for a true copy. Output and
execution validation are not. **If there is not time for that minimum, do not run it.**

### Corrected decision rule

| A's Public LB vs comparator | reading | action |
|---|---|---|
| **> comparator** | this reproduction, under our conditions, beats our incumbent | adopt as parent; consider arm B once |
| **== comparator** | no measurable difference at 3 decimals; **not** proof of identical predictions | stop the family; do not launch B |
| **< comparator** | **our frozen reproduction underperformed** — says nothing about the author's claim | revert to incumbent; stop the family |

**Bounds:** at most **2** exp_063 runs total (A, and B only on an explicit further decision); at most
**1** hidden-rerun retry for A, then the route is abandoned; **no** open-ended "tune inside the
winner" — any tuning is a separate proposal. GPU ceiling **2.0 h** for the whole of exp_063 against
10.921187 h discretionary.

### Gates (unchanged, none waived)

Strategy CONSENSUS → user authorization of the direction → fresh experiment-specific Codex
admission PASS → snapshot smoke → budget reservation → ONE authorized launch → separately
authorized LB submission with a remote cap check. 3 submissions / America-New_York day; 0 used
2026-09-24.

## 3. Where I still disagree with Codex

Codex says "choose (b): finish exp_062 first, then decide." I accept that **as the promotion and
comparator rule** — nothing is adopted or submitted ahead of k2's number. I do **not** accept it as
a reason to defer the zero-GPU audit of arm A. The audit costs no GPU, no submission and no
admission slot, and with five days left, serialising read-only work behind a running kernel spends
the only resource that is actually scarce. Audit now, decide after k2.

Codex also says 0.949 may not restore a top-200 place (dated, rounded, possibly tied). Accepted —
re-entry is not a success criterion anywhere in this document.

# PLAN.md Step 0 — the division recoverability audit, reconciled

2026-09-25. Zero GPU, zero network, zero submissions. Reproduce with
`experiments/exp_065_metric_aligned_pruning/collection/reconcile_division_audit.py`.

**Verdict: the "7 of 9 division FNs are recoverable by post-processing" number does NOT survive
reconciliation. Per PLAN.md Step 0's pre-registered decision rule, Step 2 as written is CANCELLED.**

The audit and the official scorer measure different things, and the audit measures the stricter one.
Its 7 is not a count of opportunities the scorer would reward.

---

## 1. The arithmetic reconciliation

| stem | scorer tp/fp/fn | GT = tp+fn | audit rec / miss / p_unm | non-repro | ⇒ repro_ok | consistent? |
|---|---|---|---|---|---|---|
| 44b6_12dfb391 | 0/0/1 | 1 | 1 / 0 / 0 | 1 | 0 | yes |
| 44b6_267148e4 | 0/0/1 | 1 | 1 / 0 / 0 | 1 | 0 | yes |
| **44b6_2a2eff9f** | **1/1/0** | **1** | **1 / 0 / 0** | **1** | **0** | **NO** |
| 44b6_341df25f | 0/0/1 | 1 | 1 / 0 / 0 | 1 | 0 | yes |
| 6bba_062c8d37 | 1/1/0 | 1 | 0 / 0 / 0 | 0 | 1 | yes |
| 6bba_07e24132 | 0/0/2 | 2 | 1 / 1 / 0 | 2 | 0 | yes |
| 6bba_085bf656 | 0/0/1 | 1 | 0 / 1 / 0 | 1 | 0 | yes |
| 6bba_09961292 | 1/0/3 | 4 | 2 / 1 / 0 | 3 | 1 | yes |

- **The denominators agree: 12 GT division events** both ways. The audit is not miscounting the universe.
- Derived `reproduced_ok` = 2, matching the audit's own total of 2, against the scorer's `div_tp` = 3.
- **The whole discrepancy is one stem, `44b6_2a2eff9f`:** the scorer counts its single GT division as a
  **true positive**, while the audit classes it as `recoverable_by_postprocess` — which by construction
  means *the matched predicted parent did not emit two child edges*.

That single conflict is the thread that unravels the optimistic reading.

## 2. Why they disagree — the scorer's criterion is component-level, the audit's is node-level

`compute_division_confusion` (notebook cell 8, lines 100–187) awards a TP as follows:

```python
anchor_candidates = [gsrc]                          # the GT parent ...
if gsrc in gt_in:
    anchor_candidates.append(gt_in[gsrc])           # ... OR the GT parent's own parent
...
for child in children[:2]:
    lineage = lineage_descendants(child)            # ALL descendants of each daughter
    hit_comp_ids = {components[p_id] for gt_id in lineage if ...}
...
found = any(
    comp_id in lineage_hit_components[0]
    and comp_id in lineage_hit_components[1]
    and comp_id in fork_components                  # SOME node with out-degree >= 2, anywhere in it
    for comp_id in anchor_comp_ids
)
```

So a division scores as found when **one weakly-connected component of the prediction** simultaneously
(a) contains a node matched to the anchor, (b) is touched by *some* matched descendant of daughter 1,
(c) is touched by *some* matched descendant of daughter 2, and (d) contains **any** node with
out-degree ≥ 2 — **the fork need not be at the matched parent, or anywhere near it.**

The audit asks a much narrower question: does `pred_children_count[pred_parent] >= 2`.

`44b6_2a2eff9f` is an existence proof that these differ: the parent does not fork, yet the component
does, and both daughter lineages reach it. The scorer pays; the audit calls it unreproduced.

## 3. Why this kills Step 2 as written

Step 2's premise was: *seven FNs have both daughters detected, so post-process division machinery
(`dcsd010`, `diverge150`, `repd010/015/015w`) can convert them to TPs.* That premise fails on two
counts.

1. **The audit's 7 is not scorer-relevant.** It counts events whose *matched parent* lacks two out-edges.
   The scorer does not require that. So the 7 includes events the scorer may already be crediting, and
   excludes nothing it needs.
2. **More decisively — the 9 FNs failed the *loose* test.** To be an FN under the criterion above, an
   event must hit one of:
   - a daughter lineage with **no matched node at all** in any component → detection-limited;
   - **no anchor match** → detection-limited;
   - the anchor's component contains **no fork anywhere** → a fork really is missing;
   - the two daughter lineages land in **different components** → **fragmentation**.

   The post-process division levers only address the third of those. They add or accept forks. They do
   not merge fragmented components and they do not create missing detections. A criterion this
   permissive still rejecting 9 of 12 events says the deficit is mostly structural, not a threshold.

And fragmentation is precisely the territory where this project has already failed once with a real
local gain: **exp_055's joint cut-and-reconnect repair produced +0.0148537 on the frozen local proxy
and moved the Public LB 0.000.**

## 4. The other finding, which is a caution not an opportunity

**Every `div_fp` sits on a stem that also has a `div_tp`** — `44b6_2a2eff9f` (1/1/0) and
`6bba_062c8d37` (1/1/0); the third TP stem `6bba_09961292` has fp=0. Read with the FP rule at lines
178–185 — a predicted fork whose matched GT node *is* a GT division source but is **not** the one
already credited as a TP — this is the signature of a fork landing on the **wrong node near the right
place**, not of independent spurious divisions.

Consequence: **"remove the 2 FPs" and "recover the FNs" are not independent levers.** A change that
relocates a fork could convert an FP into a TP, or lose a TP while removing an FP. The +0.00165-per-FP
arithmetic in `STATE.json.division_headroom_analysis_2026_09_25` assumed independence and should be
read as an upper bound only.

## 5. What would actually be needed, and why we are not doing it

To assign each of the 9 FNs to one of the four branches above requires the **validator prediction
graphs**, which the notebook holds in memory (`VAL_BASE_PROCESSED`) and never writes out. Getting them
means a new run with a dump added — roughly the validator portion of a run, and then a real
investigation on 12 events whose outcome is a *classification*, not a score.

Against four days, an unrevealed private split, and a documented precedent of a large local
fragmentation gain transferring as exactly zero, that is not a good use of the remaining budget.

**Step 2 is cancelled.** If it is ever revived, the first deliverable must be the per-event branch
assignment above, not a threshold sweep.

## 6. What this does not change

- `div_tp = 3 / 12` and `div_fn = 9` across all 30 measured configurations still stand.
- The division term is still worth 0.1, and perfect divisions would still be worth +0.0786. The prize
  was never the issue; **reachability** was, and this is the measurement that settles it against us.
- Steps 1, 3, 4 and 5 of `PLAN.md` are untouched. Step 1 (`cx03`) remains the cheapest next action.

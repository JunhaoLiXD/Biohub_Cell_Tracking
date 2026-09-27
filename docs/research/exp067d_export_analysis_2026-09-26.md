# exp067d feature export — result and analysis

**Run:** `lingxd/biohub-exp067d-temporal-export` v1, COMPLETE, 1817.7 s = **0.5049 GPU h**.
**Verdict on the run:** full success as an engineering artifact. Every gate passed.
**Verdict on the arc:** the export has measured a hard constraint the arc had not costed —
**division supervision** — and that constraint, not the code, now decides whether exp067 continues.

## 1. The run itself

| Gate | Result |
|---|---|
| Config-drift guard | PASS |
| Dependency gate (checkpoints, support manifest, V1284 head, 86 env values) | PASS, 48 package versions observed |
| Effective-configuration gate (**the one that failed in exp067c**) | **PASS — 126 globals and 23 predictor arguments** |
| Representative parent parity, `44b6_12dfb391` and `6bba_062c8d37` | identical node ids, coordinates and edge sets |
| Export integrity gate | `gate_passed: true` |
| Traceback / fatal / drift trip | none |

The exp067c fix is confirmed on real data. Eight movies exported: **186,803 nodes, 180,368 edges,
1,088,256 bounded alternatives, 179,745 reconsiderable nodes** (96.2%).

Note the parity gate's standing limitation, unchanged: it reuses the instrumented raw graphs, so it
evidences postprocessing preservation only — not detector or association equivalence.

## 2. The finding: supervision, not code, is the binding constraint

The TRAIN ground truth is **sparsely annotated**. Against 186,803 predicted nodes there are only
**5,935 GT nodes** — 3.2%.

**Matching is not the problem.** 5,881 of 5,935 GT nodes matched, **99.1%**. The frozen parent finds
essentially every annotated cell. The scarcity is in the annotation itself.

What matters for exp067 is divisions, because recovering missed divisions *is* the hypothesis:

| Split | movies | GT nodes | GT edges | matched | mothers | **usable division positives** |
|---|---|---|---|---|---|---|
| train | 6 | 3,769 | 3,671 | 3,734 | 7 | **5** |
| holdout | 2 | 2,166 | 2,080 | 2,147 | 5 | **4** |

"Usable" means mother **and both daughters** matched, which is what `train.py` requires. Geometry
gates in hypothesis generation can only reduce it further.

Per movie, mothers are: 1, 1, 1, 1, 2, 1 (train) and 1, 4 (holdout). Density is **~1.5 divisions per
movie**.

So at the current export size:

- The **link head** is fine: ~3.6k positives.
- The **division head would be fit on 5 examples and evaluated on 4.** One held-out event is 25% of
  the evaluation signal.

`train.py`'s guard is `min_division_positives = 3`, so the run would *technically* proceed. That
threshold was written as a wiring check — "is the division path connected at all" — not as a claim
that 5 is enough to learn from. Treating a passing floor as sufficiency would be exactly the error
this project has recorded fifteen times: asserting a mechanism works before measuring it.

**A link-only model is not a fallback.** Without a trained division head there is no joint
competition between continuation and division, which is the entire mechanism. What remains is an
edge re-ranking — the class of intervention this project has already measured null repeatedly
(exp_055 was already an edge intervention; 30 measured configurations left `div_tp` untouched).

## 3. The 8-movie selection is NOT a data limit

`train.py`'s own error text says so, and it is right. Repo records know **199 distinct movie stems**;
4 are the competition TEST stems, so roughly **195 TRAIN movies** exist. We exported 8.

*(Confirm by listing `TRAIN_DIR` before committing to any scale-up: this count comes from repo
records, not from a direct enumeration in this run.)*

Scaling arithmetic, from this run's measured 227 s/movie:

| Movies exported | Export cost | Expected divisions (~1.5/movie) | ~Train-split positives |
|---|---|---|---|
| 8 (done) | 0.50 h | 12 | 5 |
| 24 | ~1.5 h | ~36 | ~27 |
| 48 | ~3.0 h | ~72 | ~54 |
| 96 | ~6.1 h | ~144 | ~108 |
| ~195 (all) | ~12.3 h | ~290 | ~230 |

Budget remaining: **16.75 GPU h**, so even the full sweep fits. The 5400 s watchdog caps a single
kernel at roughly **23 movies**, so anything larger must be sharded across kernels.

## 4. What this means with the deadline at 2026-09-29

Scaling the export is affordable in GPU. It is **not** obviously affordable in time. Converting
exp067 into a Public LB number still needs, in order: sharded export → train the head → decode the
held-out movies → evaluate against the parent metric → build a *separate* inference notebook whose
own output is the arm (notebook-only competition) → run it → submit. That is the full admission
cycle again, on an arc whose mechanism would rest on ~50-230 division examples.

Set against the project's own recorded expectation — "a realistic outcome for these four days is
0.953-0.955" and "0.96+ has no evidenced path from here" — the probability of exp067 producing a
scoring submission before close is low, and it competes for the remaining days with two items that
cost nothing.

**Recommendation: bank the export and stop exp067 before the deadline.** Not because it failed — it
did not — but because its remaining path is long and its mechanism is supervision-starved at any
export size reachable in three days. Resume it after the close if the work continues.

The two items that should take precedence, both already in PLAN.md:

1. **Needs a human, cannot be done from here:** verify on the competition site whether final
   submissions must be selected manually, and that the 0.953 x138 submission **56535761** is
   selected. Losing a secured 0.953 to an unselected final is a strictly larger risk than any
   +0.001 still on the table.
2. **PLAN Step 5, zero GPU:** read the three unanalysed public notebooks. Unaffected by GPU
   contention and the only remaining item with a plausible cheap upside.

## 5. If the user chooses to continue exp067 anyway

The honest minimum that would make the division head worth training is roughly **48-96 movies**
(~54-108 train positives, 3.0-6.1 GPU h, 3-5 sharded kernels). Below that the head is fit on too
few events to distinguish a learned division policy from noise, and the held-out evaluation cannot
resolve a difference either.

Two things must be decided before spending it, not after:

- **A pre-registered read rule**, in the PLAN Step 1 style, fixed before the numbers arrive.
- **Which movies.** The split must be frozen before scoring and must not be chosen by label outcome.
  Note the current pool is historically label-enriched, so a wider draw changes the annotation
  density distribution and the proxy is not comparable to the harvested held-out table.

## 6. Artifacts

- Output: `.private/runtime/exp067d_out/` (8 `.npz` evidence files, 8 `.final.npz` graphs, 8 label
  sets, `metrics.json`, full kernel log).
- Record: `experiments/exp_067d_temporal_feature_export_v4/experiment.json`, state `EVALUATED`,
  0.5049 GPU h booked, reservation released.
- Admission: **Codex review WAIVED BY USER, `verdict: NO_PASS`.** No PASS exists for this run and
  none is claimed. If the arc resumes, that gate should be closed post hoc before anything is built
  on the export.

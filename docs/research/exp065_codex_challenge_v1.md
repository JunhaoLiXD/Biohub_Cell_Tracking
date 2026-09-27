# exp_065 — Codex strategy challenge v1 — REVISE

Reviewer: Codex `gpt-6-astra`, effort low, read-only sandbox. Date: 2026-09-25.
Target: `docs/research/exp065_metric_aligned_pruning_proposal.md` (v1).
Invocation: `codex exec --ephemeral --sandbox read-only --skip-git-repo-check -m gpt-6-astra -c model_reasoning_effort=low -`

**VERDICT: REVISE.** Seven blocking `[CORRECTNESS]` findings. No CONSENSUS; v1 does not authorize
anything.

**Claude Code's independent verification, per the standing rule that a reviewer's factual claims are
checked against the repository before being accepted: ALL SEVEN blocking findings are GENUINE.**
Each was re-derived from the notebook sources; see the verification note appended at the end of this
file. Codex's shell tool failed to initialize and it worked through read-only Node access; that did
not impair the findings.

---

VERDICT: REVISE

## Verdict

The measurement-first strategy is reasonable, and the headline arithmetic largely reproduces. However, the proposed execution contract does not currently deliver its promised control artifact or reliably apply its settings. The source also contradicts several mechanistic claims, and the supplied analysis script does not implement the notebook’s prefix guard. These are concrete correctness problems, not objections to accepting a no-submission outcome. I cannot give strategy-level CONSENSUS to v1.

Notebook references below use zero-based cell indices and one-based source lines. “Vehicle” means `docs/research/public_notebook_archive/optimized-biohub-max-score.ipynb`; “proposal” means `docs/research/exp065_metric_aligned_pruning_proposal.md`.

## Blocking [CORRECTNESS] findings

1. **Empty preset/cache settings do not disable those paths.**  
   The proposal explicitly concludes that empty strings make these branches dead. The vehicle instead searches `/kaggle/input/*/ppsweep_selected.json` **when the setting is empty**, loads a usable preset, and applies its overrides before the base write. It similarly auto-discovers validator caches. This is an added, executing path capable of changing the base graph despite the declared off settings. Matching dataset names alone does not establish that their mounted contents cannot trigger it.  
   **References:** proposal:78–83; vehicle cell 0:174–226; cell 5:2871–2876.

2. **The promised base control artifact is never preserved.**  
   `write_test_submission("base")` does precede validation, but `tag` changes the statistics label—not the output filename. Every invocation opens the same `SUBMISSION_PATH` with `"w"`. Selection subsequently rewrites that file. There is no `submission_base.csv` creation or backup anywhere in the notebook. Thus the described one-line-only vehicle does not deliver Gate 1’s control after a successful sweep. A failure before rewriting preserves the base; the archived final-print crash happened **after selection and rewriting**, so it does not demonstrate preservation of the base.  
   **References:** proposal:178–201, 231, 297; vehicle cell 5:2733, 2859, 2876; cell 10:249–255.

3. **External environment settings are overwritten, and the local configuration gate contradicts Run 1.**  
   Cell 0 unconditionally assigns `FAST_TIER="1"`, `VALIDATOR_ENABLE="1"`, and pruning levers to zero. Setting these externally before execution therefore does not produce the proposed full sweep or deterministic Run 2. No later override mechanism is specified. Furthermore, requiring all 89 parent values conflicts with Run 1 intentionally changing `VALIDATOR_ENABLE` from zero to one.  
   The claimed repair-deadline difference is also incorrect: the vehicle’s initial value is already **27000**. The 30600 assignment occurs during the later selected-config rewrite, not initial configuration.  
   **References:** proposal:61–69, 183–207, 271–279; vehicle cell 0:67–69, 104–138; cell 10:252.

4. **The analysis script does not reproduce the author’s prefix guard.**  
   The notebook computes each prefix’s adjusted-edge average using that candidate’s weights, then adds division Jaccard from **pooled TP/FP/FN**. The script instead uses base weights and averages per-movie division Jaccards. Both differences matter. For `dcsd015`, the script’s 6bba proxy improvement is **+0.0104716**, while the notebook’s is **+0.00299270**. For `ep015`, the 44b6 regression is **−0.00969193** versus **−0.00849388**. The current reject conclusion survives, but this is not the promised executable gate for future candidates.  
   **References:** proposal:306, 310–313; `analyze_sweep_table.py`:98–116; vehicle cell 9:126–134; cell 10:115–125.

5. **`tight55` is an unchanged control, not evidence that the tight-distance path is inert.**  
   The parent already sets `MOTION_RELINK_TIGHT_UM=5.5`; the candidate sets exactly the same value. Its identical results cannot establish that flow handles every decision or close other tight-distance experiments. The observed equality for `vel075` and `rescue085` is real, but metric equality alone also does not establish graph-byte equality or universal inactivity.  
   **References:** proposal:33–34, 359; `biohub-x138.ipynb` cell 0:76; vehicle cell 10:6; recon:105–110.

6. **The count mechanism is described incompletely, and universal profitability is unsupported.**  
   The implemented multiplier is `1 − 0.1 × (t_pred − t_true)/t_true`, with a floor on the resulting score. Underprediction is **rewarded**, not merely unpenalized. Pruning improves that multiplier, but can reduce the complete score—as the two `ep015` losses demonstrate.  
   Also, the cited **0.752** ratio for `44b6_12dfb391` is the **ep015 result**; base is **0.762630**. The count-target function adapts to its own confident core, not ground-truth excess. For example, 800 predicted nodes, a 500-node core and `frac=0.06` imply a target of 530 even if true count is 1,000. It offers no underprediction protection.  
   **References:** proposal:30–38, 95–109; vehicle cell 8:74–77; cell 5:2395–2406; `validator_results.csv`, base/ep015 rows for `44b6_12dfb391`.

7. **The promised measurement size and selection scope are inconsistent.**  
   There are **41 declared candidates excluding base**. The archive contains base, 12 declared candidates, and one dynamically generated combination: therefore **29**, not 27, declared candidates remain unmeasured. A complete run produces 42 configurations including base, potentially 43 with a generated combination—not 41.  
   Further, Gate 2 ranks all candidates, including division and geometry interventions declared out of scope, while Run 2 promises a “single winning override” even though several eligible candidates change multiple parameters. The admissible experiment is therefore not uniquely specified.  
   **References:** proposal:163–166, 196–197, 205–207, 278, 301, 355–359; vehicle cell 10:4–90, 167–171.

## Non-blocking findings

1. **[DESIGN] The jackknife is a useful fragility screen, not evidence of reliable transfer.**  
   Rejecting the largest observed effect is not itself too strict; relaxing the rule because `ep015` fails would be unconvincing. But all eight leave-one-out estimates are highly dependent, and selecting among 41 candidates remains optimistic. The script also globally renormalizes after deletion, changing the prefix mixture rather than preserving 37.3%/62.7%. For the stated four-movie target, a more directly relevant sensitivity analysis is all **36 subsets containing two movies from each prefix**, alongside equal-movie and fixed-prefix weighting. Report downside and concentration; these subsets are not independent confirmation data.  
   **References:** proposal:301–308; `analyze_sweep_table.py`:83–95.

2. **[DESIGN] “Test-reweighted” is a modelling assumption, not recovered official test weighting.**  
   The 37.329%/62.671% calculation is correct, but its inputs are **predicted output-node counts**. The validator weights are edge-confusion denominators, which can change with the candidate. These are different quantities. Likewise, observed test densities do not establish the private evaluation distribution.  
   **References:** proposal:136–139; exp_064 `collection/metrics.json`, `details.nodes_per_dataset`; vehicle cell 8:294, 300–310.

3. **[RISK] Byte equality on four visible movies would establish narrower equivalence than claimed.**  
   It would validate those output bytes under that execution, not prove all added paths inert or establish hidden-rerun equivalence. The governor is not a hard wall: `WALL_BUDGET_S` is reporting-only, the per-dataset cap is disabled, and the sweep checks deadlines between candidates. A long candidate can overrun.  
   **References:** proposal:127–129, 244–249; vehicle cell 0:126–131; cell 10:144–149.

4. **[RISK] Hash verification does not establish training provenance or independent holdout status.**  
   All six manifest entries matched. That establishes archived byte integrity, not which exact source/environment produced the outputs or whether V1284 training excluded these movies. The selector explicitly prioritizes training movies containing divisions. Unchanged pooled division recall across 14 configurations does not prove recall is “upstream-locked” for every untested intervention.  
   **References:** proposal:35–36, 260–265, 350–358; vehicle cell 7:34–57; `SHA256SUMS_amanatar_v9.txt`:1–6.

5. **[SCOPE] I support prioritizing a bounded measurement over another uncalibrated LB probe.**  
   Approximately three hours is defensible within the supplied budget, provided the control and execution problems are resolved. I do not see evidence compelling immediate priority for `readmit-v1`. However, running all geometry/division candidates despite declaring those families closed broadens both runtime and selection exposure. The result would map this finite grid—not definitively map post-processing.  
   **References:** proposal:168–172, 284–293, 343–363.

## What I verified and found correct

- All six SHA256 manifest entries match their archived files.
- The CSVs contain **14 configurations × 8 stems = 112 rows**.
- All 14 aggregate rows satisfy `proxy = adjusted_edge_jaccard + 0.1 × division_jaccard`, with zero residual.
- Independent JavaScript recomputation of the analysis logic gives `ep015` **+0.0023641441**, worst leave-one-out **−0.0029492411**, and **60.5613%** gross-positive concentration.
- The other quoted leave-one-out values reproduce apart from minor rounding: dropping `44b6_2a2eff9f` gives **+0.00236885**, conventionally rounded to **+0.00237**.
- Every non-label CSV field matches base for `tight55`, `vel075`, and `rescue085`.
- Pooled division counts are **TP=3, FN=9** for all 14 configurations.
- The count multiplier improves on all eight `ep015` stems.
- The six named pruning/sweep identifiers are absent from x138.
- The 24-line enumeration matches a nonblank exact-line-absence comparison, but that comparison does not establish execution equivalence.
- The base write precedes validation. The `_v6env` defect is in final printing; its assignment is cell 11, **line 44** under one-based numbering.
- No measured candidate clears the proposed aggregate-plus-jackknife conditions.

## What I could not verify

I did not execute GPU inference, establish byte reproduction, inspect mounted Kaggle dataset contents, authenticate current remote standings or budgets, or verify private-test composition and V1284 training provenance. I verified the archived validator’s formula, not its equivalence to an independently retrieved official scorer.

The shell tool failed to initialize. I completed filesystem inspection, hashing, source comparison, and independent CSV arithmetic through read-only Node access. No files were changed, and no launches or submissions occurred.

---

## Claude Code's verification of each blocking finding (2026-09-25)

Re-derived independently from the notebook sources. **All seven are genuine.** Two of them correct
errors that had already propagated into `STATE.json`, `HANDOUT.md`, the recon document and the
auto-memory; those records were corrected in the same pass.

1. **Auto-attach on empty settings — CONFIRMED, and I had it exactly backwards.**
   `vehicle` cell 0 line 178 reads
   `if FROZEN_PRESET_OVERRIDES is None and not os.environ.get("BIOHUB_FROZEN_PRESET_JSON","").strip():`
   — the **empty string enables** a glob of `/kaggle/input/*/ppsweep_selected.json`, and a valid hit
   is loaded and applied before the base write (lines 179–201). Line 202 does the same for
   `BIOHUB_VAL_PRED_CACHE_DIR` via `*/cache_key.txt`. My §1/§3.1 claim that empty strings leave these
   branches dead is false.

2. **Base control artifact not preserved — CONFIRMED.** `write_test_submission(tag)` is cell 5 line
   2717 and always opens `SUBMISSION_PATH` (`/kaggle/working/submission.csv`) with `"w"` at line
   2733; `tag` is only a statistics label. Cell 10 rewrites the same path after selection. Codex is
   also right that amanatar's crash cannot serve as evidence of preservation: it occurred **after**
   selection and rewriting, so their recovered `submission.csv` is the rewritten `dcsd015` artifact,
   not the base.

3. **Cell-0 assignments are unconditional — CONFIRMED, and my claimed deadline difference does not
   exist.** Every setting is a bare `os.environ[...] = "..."`, so pre-setting variables outside the
   notebook is overwritten; Run 1 and Run 2 cannot be configured "at environment level" as v1
   describes. Separately, cell 0 line 69 sets `BIOHUB_REPAIR_DEADLINE_S = "27000"` — **identical to
   x138**. The `30600` I reported comes from cell 10 line 252, inside the pass-2 *rewrite* path. My
   extraction took the last occurrence in a flattened source and I built a "fix" for a non-problem.

4. **The analysis script does not implement the notebook's guard — CONFIRMED.** Cell 9 lines 126–134
   weight by **the candidate's own** `weight` column and add
   `VALIDATOR_DIVISION_WEIGHT * edge_jaccard(pooled tp, fp, fn)` — a single Jaccard over **pooled**
   counts. `analyze_sweep_table.py` used base weights and averaged per-movie `div_jaccard`. Both are
   wrong. The reject conclusion survives, but the gate is not the promised executable one.

5. **`tight55` proves nothing — CONFIRMED, and this is the most consequential finding.**
   `biohub-x138.ipynb` cell 0 line 76 and `vehicle` cell 0 line 71 both set
   `BIOHUB_MOTION_RELINK_TIGHT_UM = "5.5"`, and the `tight55` candidate sets **5.5**. The sweep never
   varied the variable; the identical row is a self-consistency check. **The claim "`MOTION_RELINK_TIGHT_UM`
   is bit-for-bit inert" is withdrawn.**
   The other two survive and are real: `MOTION_RELINK_VELOCITY_WEIGHT` defaults to **0.5** and
   `vel075` sets 0.75; `SHORT_TRACK_RESCUE_MIN_MEAN_EDGE_PROB` is set to **0.88** and `rescue085` sets
   0.85. Both are genuine changes with identical results on all 8 stems.

6. **The count adjustment is mis-stated — CONFIRMED.** Cell 8 line 77:
   `return max(0.0, jaccard * (1.0 - a * (t_pred - t_true) / t_true))` with `a = 0.1`. For
   `t_pred < t_true` the multiplier exceeds 1, so under-prediction is **actively rewarded**, not
   merely unpenalised. The `0.752` ratio I attributed to base for `44b6_12dfb391` is ep015's
   (44133/58672); base is **0.76263** (44745/58672). And Codex is right that
   `prune_to_node_count_target` budgets against **its own confident core**, not against ground-truth
   excess, so it offers no protection on an under-predicting movie — my §2 argument that it repairs
   ep015's failure mode is not supported and must be downgraded.

7. **Counts are wrong — CONFIRMED.** `PP_CANDIDATES` holds **41 entries excluding base** (7 in the
   base dict + 34 added under `PPSWEEP_EXTENDED`). The archive has base + 12 declared + 1 dynamically
   generated combination = 14 rows, so **29** declared candidates are unmeasured, not 27, and a full
   run yields 42 configurations including base (43 with the generated combination), not 41.

**Nothing in the review was rejected.** The non-blocking `[DESIGN]`/`[RISK]`/`[SCOPE]` findings are
accepted as written and carried into v2.

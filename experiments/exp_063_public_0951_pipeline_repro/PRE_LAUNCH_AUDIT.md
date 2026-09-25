# exp_063 pre-launch audit — third-party verbatim reproduction

Auditor: Claude Code, 2026-09-24, zero GPU. Target: the snapshot at
`experiments/exp_063_public_0951_pipeline_repro/snapshot/source/biohub-0-951-sota-deepcenter-fast-ilp-19m.ipynb`,
SHA256 `fb2b1cd4d9612d333eb2e8ad6c0106646ac2429c05ccfce5997179135a228734` — byte-identical to the
in-repo archive at `docs/research/public_notebook_archive/`.

This audit exists because Codex rejected "we authored nothing" as a safety argument: we inherit
every upstream defect. The list below is Codex's required minimum, accepted in full.

## Results

| # | audit item | result |
|---|---|---|
| 1 | frozen hash + acquisition metadata archived in-repo | **PASS** — `fb2b1cd4…`, pulled 2026-09-24, `SHA256SUMS.txt` + `kernel-metadata.json` committed. Motivated by a sibling notebook going 403 mid-analysis. |
| 2 | mounted dataset versions | **PASS** — three Pilkwang checkpoints **identical to the ones our parent already mounts**, plus `giorgosi/biohub-divnet-v2`. |
| 3 | docker image | **PASS** — digest `sha256:37c64f7d…`, the **same image exp_060 and exp_062 ran on**. Proven environment. |
| 4 | ground-truth access on test | **PASS** — no GT/label/solution read. The notebook's own receipt records `ground_truth_accessed: False`, and independently there is no `solution.csv` or `sample_submission` read anywhere. |
| 5 | specimen / video blindness | **PASS** — all four hidden-test dataset names (`44b6_0113de3b`, `44b6_0b24845f`, `6bba_05b6850b`, `6bba_05db0fb1`) appear **zero** times, full or by stem. Discovery is dynamic: `TEST_DIR.iterdir()` over `*.zarr`. |
| 6 | network egress | **PASS** — `enable_internet: false`; no `requests`, `urlopen` or any HTTP call. |
| 7 | output schema | **PASS** — `SUBMISSION_COLUMNS = ["dataset","row_type","node_id","t","z","y","x","source_id","target_id"]` plus a leading `id`. **Identical to the schema our own 0.947 submission uses.** |
| 8 | writes confined to the working dir | **PASS** — zero writes outside `/kaggle/working`. |
| 9 | hardcoded score / result short-circuit | **PASS** — the only `0.951` / `0.948` occurrences are markdown title and comparison-table prose. No code path returns or gates on a score. |
| 10 | `subprocess` / `exec` / `eval` use | **PASS** — `subprocess` only, for the same sharded dual-GPU inference pattern our parent already uses. No `exec`/`eval` of external content. |
| 11 | resume / cache hazard (the exp_062 trap) | **PASS, and notable** — there is **no resume or prediction-cache machinery at all**. The exp_062 signature-collision hazard structurally cannot occur here. |
| 12 | checkpoint integrity self-reporting | **PASS** — the notebook computes and writes real SHA256s for the primary, secondary and DeepCenter checkpoints into `bidirectional_production_runtime_integrity.json`. Verifiable at collection. |

## The one OPEN item

**`giorgosi/biohub-divnet-v2` training provenance is unverified.** The dataset is public (5.18 MB,
481 downloads, last updated 2026-09-07) and mounts fine, but — exactly as Codex put it — *public
accessibility is not evidence of permitted training provenance*. We cannot establish what it was
trained on.

Risk assessment, stated rather than hand-waved: the competition's **test labels are not public**,
so a DivNet trained on them is not a realistic scenario; training on the provided training split
would be ordinary and permitted. The residual risk is therefore low but **not zero, and not
closed**.

Two mitigations exist and neither is free:
- Set `BIOHUB_DIVNET_VERIFY=0`. This closes the item completely, but it **breaks verbatimness** —
  it would no longer be the pipeline whose 0.951 is claimed, and it removes one of the five stacked
  mechanisms. It also re-introduces authored deviation, which is the thing this route exists to
  avoid.
- Run verbatim and record the item as open. DivNet acts on **division**, the 0.1-weighted term, so
  on this project's own repeated evidence it is the mechanism least likely to be driving any LB
  movement we observe.

**Recommendation: run verbatim, item recorded as open.** Flagged for the reviewer to overrule.

## What this audit does NOT establish

- **Not** that 0.951 is real. That is a title claim by an author absent from the LB top 200
  (rank-200 cutoff 0.949) on a notebook with 7 votes.
- **Not** that the code is correct, only that it is compliant and structurally sane on the axes
  above. ~2450 lines are not line-by-line reviewed and will not be in the time available.
- **Not** private-set behaviour. Public LB movement does not establish private-set movement.
- **Not** causal attribution. Five mechanisms are stacked; a gain cannot be assigned to any one.

## Post-run validation required at collection (not optional)

`submission.csv` exists, non-empty, exact 10-column schema, all four hidden-test datasets covered,
SHA differs from parent `d3453380`; the runtime integrity receipt present with
`ground_truth_accessed: false` and resolvable checkpoint SHA256s; **measured** wall-clock recorded
and reconciled into `GPU_BUDGET.json` (the "19m" claim is unverified and must not be assumed).

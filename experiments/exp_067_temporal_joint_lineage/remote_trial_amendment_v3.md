# exp_067 — remote-trial amendment v3 and CONSENSUS record

**Status: CONSENSUS (Claude Code strategy + Codex objections of 2026-09-26, all five accepted).**

**Scope of this consensus: the REMOTE first trial of exp_067** — what the first Kaggle run is
allowed to do, what it must prove before it may run, and what it may instead prove while running.
This is the scope that
[`revision_acceptance_v2.md`](revision_acceptance_v2.md) deliberately did **not** cover: its
opening line limits itself to "local architecture, local implementation, local validation". That
gap is exactly what the exp067b admission review called a blocker, and it is what this record
closes. `revision_acceptance_v2.md` remains in force unchanged for everything local; nothing in it
is reopened, weakened or rewritten here, and neither are the frozen exp067a/exp067b snapshots,
configs and reviews.

Execution record this amendment governs: **`exp_067c_temporal_feature_export_v3`**.

---

## 1. The amendment, stated exactly

The disputed move, in one sentence:

> **Real-data parent parity moves from a pre-launch prerequisite to an acceptance gate evaluated
> inside the first remote run.**

What that means concretely, and what it does not:

| | Pre-launch (before this amendment) | Remote acceptance gate (this amendment) |
|---|---|---|
| Parent notebook identity | SHA-pinned, reverse-patch parity proven locally | unchanged, still pre-launch |
| Patched predictor source | real patch chain replayed and compiled locally | unchanged, still pre-launch |
| Checkpoint / support-repo identity | expected hashes frozen from the exp064 receipt | asserted against the **observed** runtime hashes, before inference |
| Effective configuration | *(was: recorded after the fact)* | **asserted** before inference; see §3 item 2 |
| Parent postprocessing parity on real movies | *(was: claimed as a prerequisite)* | **measured** in-run, one movie per prefix, and a failure stops the run |

The reason the parity check cannot be a pre-launch prerequisite is not convenience. It needs the
competition movies, the mounted checkpoints and a CUDA device. There is no local environment in
this project that has any of the three, so a "prerequisite" phrased that way could only ever have
been satisfied by prose. Making it a gate that runs on the real data, and that fails the run when
it fails, is strictly more evidence than the prerequisite it replaces — not less.

What the amendment does **not** do, stated so it cannot be read broadly later:

- It does not relax any leakage, provenance, hash-integrity, budget, leaderboard or promotion gate.
- It does not authorize a leaderboard submission (`leaderboard.authorized: false`).
- It does not authorize training, promotion, or a second attempt after a failure.
- It does not claim the parity gate proves detector or association equivalence. It reuses the
  instrumented raw graphs, so it evidences **postprocessing preservation only**. That limitation is
  carried in the config, in the notebook comment, and in the metrics field
  `representative_parent_parity_scope`, so a later reader cannot inherit a stronger claim than the
  evidence supports.

## 2. Why the remote trial is worth running at all

The first run is a **prerequisite feature export**, not a test of the accuracy hypothesis. It runs
the frozen exp064 pipeline on eight fixed TRAIN movies and saves the measured features,
alternatives, final graphs and allowed labels that the learned joint-lineage head needs as input.
Without it there is nothing to train on. It produces no submission and no score, and the metrics it
writes are a binary engineering gate whose `metric_meaning` says so in the artifact itself.

Cost: a planned 2.0 GPU h against 17.387 h remaining, bounded by a 5400-second in-notebook watchdog
that kills descendant predictor processes. No automatic retry.

## 3. Codex objections of 2026-09-26 and Claude's response

Source: [`../exp_067b_temporal_feature_export_v2/review.md`](../exp_067b_temporal_feature_export_v2/review.md)
(VERDICT: BLOCK, 13:42:48 UTC). All five required changes are **accepted in full**; none is
disputed, and none is answered with prose alone where code was the honest answer.

**1. Record explicit consensus on the remote-trial amendment.** Accepted. This document is that
record. The objection was correct on the facts: `revision_acceptance_v2.md` §scope limits itself to
local work, so citing it as the strategy record for a remote run overstated what had been agreed.
`configs/exp_067c_temporal_feature_export_v3.yaml` now points `strategy_record` and
`revision_record` here instead.

**2. Assert the effective predictor arguments and resolved postprocessing settings against the
frozen parent, allowing only declared export differences.** Accepted, and this was the substantive
one. The exp067b gate checked `os.environ` assignments in a cell that runs *before* the
postprocessing globals resolve, then merely recorded those globals afterwards — which is the
"stale notebook prose" failure mode the reviewer's own checklist names. v3 replaces that with:

- `scripts/exp067_parent_config.py`, a side-effect-free static evaluator that resolves the frozen
  exp064 notebook's **own** assignments against its **own** frozen environment. The expected table
  is derived from the parent source at build time; it is not retyped, so it cannot drift from the
  parent by hand. It refuses to resolve a global against an environment value a later cell rewrites.
- An **effective-configuration gate** injected into the validator cell after every configuration
  global is bound and after `predict_val_cmd` is fully assembled, but **before** the predictor
  subprocess starts. It asserts 126 resolved globals and the complete 23-argument predictor argv.
  The argv is rebuilt from the frozen expectation rather than from the live globals, so a drifted
  global cannot validate itself. Type is compared as well as value, so a bool cannot stand in for
  the int it equals.
- Exactly **one** declared difference in each direction, checked rather than exempted:
  `BIOHUB_VALIDATOR_ENABLE` `'0' -> '1'` and the `VALIDATOR_ENABLE` `False -> True` it produces.
  The export reaches TRAIN movies only through the validator path that x138 switches off; that is
  the whole of the intended drift. The gate also fails on any `BIOHUB_*`/`V1284_*` key the frozen
  parent never set, apart from additive `BIOHUB_EXP067_*` keys.
- What is deliberately **not** asserted is enumerated in the artifact, not dropped silently: 19
  Kaggle-mount paths, loaded model bundles, comprehensions and wall clock, each with its source
  text, in `effective_configuration.unasserted_globals`.
- A correctness fix fell out of this. exp067b asserted `BIOHUB_DEEPCENTER_CHECKPOINT` against the
  cell-0 literal, but parent cell 3 **overwrites** that key with the materialized path it resolves.
  v3 treats the three runtime-resolved keys (`BIOHUB_DEEPCENTER_CHECKPOINT`,
  `BIOHUB_SECONDARY_WEIGHTS`, `V1284_HEAD`) as presence-and-file checks and records the observed
  values; their bytes are already pinned by the checkpoint hashes asserted in the same cell.
- The gate cannot be skipped: the export asserts `VALIDATOR_ENABLE is True and val_stems` at the top
  of the cell, and the final metrics gate refuses to pass unless the configuration gate ran.

**3. Persist observed dependency hashes and package versions in the final metrics.** Accepted. The
dependency cell now builds `_x67_observed_dependencies` — observed checkpoint hashes, observed
support-repo manifest hash and file count, materialized paths, the observed V1284 head hash, the
runtime-resolved environment, observed versions for every package in the parent's `PACKAGE_SPECS`
plus torch/numpy/scipy, the Python version, platform, torch CUDA version and GPU names — and the
metrics contract carries it beside `expected_parent_checkpoints` and
`expected_support_repo_python_manifest_sha256`. Expected and observed are both present, separately
labelled.

**4. Correct the split name and the reservation statement.** Accepted; both were wrong.

- The split is a **within-prefix movie holdout**: six TRAIN movies fit the head, two are held out,
  both prefixes on both sides. It is not leave-one-movie-out cross-validation and not a cross-domain
  split, and it therefore cannot establish cross-domain generalization. Renamed in
  `splits_v2.json`, in the config (`validation.split_protocol`), in the metrics contract, and in
  `scripts/exp067/supervise.py`, where the constant itself was called `PROTOCOL_LOMO`. The old
  spelling stays accepted as a legacy alias so the frozen historical manifests keep loading.
- The budget is **planned, not reserved**. `admission_revision_v2.md` said "Two GPU hours reserved"
  while the record said `reserved: false`; the prose was simply inaccurate. The v3 config says the
  controller reserves the 2.0 h at the launch gate, and the reservation is a real controller step
  in the sequence below, not a sentence.
- The limited scope of the representative parity check is retained verbatim in the config, the
  notebook and the metrics.

**5. Complete snapshot smoke and controller reservation before launch.** Accepted. See §5.

## 4. What this amendment is evidence of, and what it is not

Stated plainly, because the temptation later will be to read it as more:

- It is evidence that the export is bounded, provenance-checked and honestly labelled.
- It is **not** evidence that the learned joint-lineage model will improve anything. No accuracy
  claim exists for exp_067 and none may be made until the head is trained on the six training
  movies and decoded on the two held-out ones, with the parent metric and graph audits.
- A later score from this split is a **biased local proxy**. The movie pool inherits historical
  label enrichment and the frozen backbone's overlap with it is unknown. exp055's proxy/LB
  divergence is the standing reason to distrust proxies of this shape.

## 5. Gates that still stand between this record and a launch

In order, none waived:

1. Fresh experiment-specific Codex admission review of `exp_067c_temporal_feature_export_v3`,
   through `scripts/request_codex_review.py`, recording a real `PASS`. No waiver and no fabricated
   receipt. A `REVISE`/`BLOCK` stops here and returns to this document.
2. Controller snapshot smoke (`scripts/run_smoke_test.py`) on the frozen snapshot.
3. Explicit controller budget reservation of 2.0 GPU h.
4. One user-authorized launch. The user authorized a Kaggle trial for this work on 2026-09-26; the
   controller gates above are not a substitute for it and it is not a substitute for them.
5. Leaderboard submission and promotion remain separately unauthorized.

## 6. Counter-signature

Claude Code authored the amendment; Codex challenged it in the exp067b admission review; Claude
accepted all five objections above without dispute and implemented the three that were code.
**CONSENSUS recorded on the remote-trial protocol.**

The countersignature for the *implementation* of these acceptances is the fresh Codex admission
review of `exp_067c_temporal_feature_export_v3` required by §5 item 1. Until that review returns
`PASS`, this record establishes agreement on the protocol and nothing about the correctness of the
v3 snapshot.

## 7. Local evidence at the time of writing

`.private/runtime/exp067_cpu/Scripts/python.exe -m pytest tests/test_exp067.py
tests/test_exp067c_admission.py -q` → **22 passed**. The 14 pre-existing behavioral tests were
re-run after the final admission revisions, which the exp067b handoff correctly flagged as not
having happened. The 8 new tests in `tests/test_exp067c_admission.py` **execute** the generated
gates rather than pattern-matching them: they check that the frozen notebook is byte-identical to
what the builder produces, that the gates run before any `subprocess` launch, and that each gate
actually rejects a drifted global, a drifted environment value, a reverted declared difference, a
stray `BIOHUB_*` key, a missing runtime checkpoint, a drifted predictor argument, a dropped
`--use-ilp`, and a stripped `PYTHONPATH`.

This is local implementation evidence. It says nothing about Kaggle runtime compatibility or about
biological accuracy.

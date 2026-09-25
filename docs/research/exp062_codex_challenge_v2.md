# exp_062 — Codex strategy challenge v2

Reviewer: Codex `gpt-6-astra`, effort low, read-only sandbox. Date: 2026-09-24.
Target: `docs/research/exp062_mutual_best_edge_association_proposal_v2.md`.

**VERDICT: REVISE** — five of six round-1 findings fixed; one left open; one newly introduced.

---

## Verdict

**REVISE.** The main round-1 corrections are substantive, but two issues remain: cache isolation is unspecified despite an actual parent resume-signature collision, and the new calibration description misidentifies both the scaling axis and the tensor receiving the bonus. These are bounded corrections, not reasons to abandon β = 0.20.

Strictly read-only; no files created or changed.

VERDICT: REVISE

## Round-1 findings: fixed or not

References below use [v2](/E:/Project/Biohub_CellTracking/docs/research/exp062_mutual_best_edge_association_proposal_v2.md). “Parent source lines” refer to decoded code-cell lines in the [immutable parent notebook](/E:/Project/Biohub_CellTracking/experiments/repro_059_public_0947_exact_copy/snapshot/source/biohub-repro059-public-0947-exact-copy.ipynb), whose JSON occupies one physical line.

1. **Fixed:** correct four-case bonus table and separate execution/probability/candidate/graph effects; no requirement that winners change (v2:146–198).
2. **Partially fixed:** separate control/candidate versions, retained PP sweep, and combined budget are correct; the explicitly requested cache isolation remains unspecified (v2:200–225, 307–324).
3. **Fixed:** exp_055’s edge intervention, actual score formula, and division headroom are acknowledged in the rebuilt rationale (v2:41–64), consistent with [exp_055 metrics:16](/E:/Project/Biohub_CellTracking/experiments/exp_055_original_score_joint_bootstrap_smoke_fix/metrics.json:16).
4. **Fixed:** displayed equality closes the probe; identical output is not submitted (v2:328–349).
5. **Fixed:** deployment exclusivity is replaced with “closest successful minimal-change deployment precedent” (v2:77–82).
6. **Fixed:** public pedigree is explicitly unverified context, not efficacy evidence (v2:173–178).

## Newly introduced defects

- **[CORRECTNESS] The new calibration account is wrong in two material ways.** `forward_scale` reduces dimension 1 of `[1,n_src,n_tgt]`, producing `[1,1,n_tgt]`: it is **per target, across sources**, not per source. It is lower-clamped at `1e-4`; the **ratios**, not `forward_scale`, are clamped to `[0.5,2.0]`. Furthermore, harmonic fusion is followed by calibrated secondary-model blending before `raw` is assigned. Thus `forward_scale` alone does not describe the actual bonus-input scale. Correct v2:134–144 and 246–254; distinguish intermediate-scale telemetry from final-`raw` telemetry. Evidence: parent source lines 1187–1232 and 1348–1363.

The unresolved cache issue belongs to round-1 finding 2, rather than being relabelled a new finding.

## Ruling on the two-version deployment design

**The architecture satisfies the single-config requirement; the complete isolation contract does not yet.**

The parent’s resume signature explicitly enumerates environment keys and contains neither new scoring mode nor beta. Matching cached predictions bypass inference (parent source lines 1669–1675); validation reuse inherits that same signature (3290–3295). Switching only the proposed environment variables can therefore reuse control predictions **if working state is retained**.

Specify either guaranteed fresh, isolated working/cache state for each version, or mode/beta/patch identity in the relevant cache signatures. This is the concrete missing portion of finding 2—not a demand for another GPU test.

**The env-gated hash assertion is sound provided the variable is actually absent during candidate execution.** Absence of an assignment in source does not itself establish absence from the process environment (v2:216–220, 287–288). Verify effective absence in the implementation review, or explicitly clear it for candidate mode. The submitted version must retain ordinary current-input integrity checks while skipping historical public-output equality.

The 3-hour reservation fits the recorded balance and protected reserve: [GPU_BUDGET.json:4](/E:/Project/Biohub_CellTracking/GPU_BUDGET.json:4).

## Ruling on the revised stop rule

**Sound.** Equality at displayed 0.947 does not distinguish cancellation, unannotated changes, or rounding; closing this probe is justified. Skipping byte-identical output is also correct.

Treat H1 as an operational hypothesis about the **displayed score**. Equality does not scientifically falsify every possible underlying benefit. Density-adaptive relinking remains a separately proposed and authorized successor.

## Verification of the two new claims

- **Sigmoid unreachability: confirmed for the frozen parent execution path.** The default is softmax; the CLI constructs `PredictConfig` without overriding activation ([predictor:72](/E:/Project/Biohub_CellTracking/references/biohub-tracking-support-pack/repo/scripts/predict_unet_transformer.py:72), [predictor:646](/E:/Project/Biohub_CellTracking/references/biohub-tracking-support-pack/repo/scripts/predict_unet_transformer.py:646)). Parent source and decoded patch anchors contain no activation override. Keeping the effective-runtime assertion is appropriate.
- **Calibration claim: partly confirmed, ultimately rejected as written.** Harmonic probability fusion, logarithm, recentering, and ratio-clamped rescaling are real. However, scaling is per target, and the subsequent `low_margin_consensus` secondary blend also contributes to `raw` (parent source lines 1003–1005, 1187–1232). The proposal stops tracing the tensor too early.

## Bottom line for the remaining five days

Keep mutual-best β = 0.20 as the next bounded probe. Correct the calibration account and make cache/environment isolation explicit, then proceed to the scoped implementation review. Neither finding warrants a beta sweep, new architecture, or expanded verification campaign. Strategy-level CONSENSUS is **not yet reached**.

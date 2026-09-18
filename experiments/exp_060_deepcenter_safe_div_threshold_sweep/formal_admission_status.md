# exp_060 — FORMAL controller Codex admission (request_codex_review.py) status

Reviewer: Codex `gpt-6-astra` low (config temporarily swapped, restored), via the controller's
generic `build_review_prompt` against the immutable snapshot. Date: 2026-09-18.

This is the MANDATED launch gate (the controller requires review.status == PASSED). It is a
DIFFERENT, generic-prompt review from the 5 custom-prompt admission rounds (admission_review_v1..v4,
which reached PASS). The formal reviewer, with fresh eyes on the real scorer, found deeper items.

## Round-by-round
- **Formal v1: REVISE** — 4 real findings: (1) nonfinite on the REAL scorer manifests as a
  missing-bypass, so the nonfinite check was dead; (2) telemetry could vanish while gate PASS;
  (3) config verification only checked MOTION_RELINK_TIGHT_UM; (4) fork survival checked only the
  candidate edge. **ALL FOUR FIXED** (missing-bypass gate; telemetry_persisted gate;
  effective-config fingerprint; both-daughter survival + exact edge diffs).
- **Formal v2: REVISE** — 2 items: (1) watchdog doesn't reap GPU subprocesses; (2) config keys
  omit active settings / permit missing / arm-to-arm only. **FIXED**: watchdog now flush+close
  metrics then psutil-reaps child processes; EXP060_CONFIG_KEYS expanded to 75 confirmed globals
  with a no-missing-key completeness gate.
- **Formal v3: REVISE** — (1) TimeoutError could be swallowed by broad `except Exception` (alarm
  one-shot) → **FIXED**: watchdog now raises `KeyboardInterrupt` (BaseException, not swallowable);
  (2) isolation evidence: arm-order/shared-input invariance is tested against a MOCK
  postprocessor, not the real GPU pipeline; (3) config guard checks cross-arm equality, not
  equality vs a complete canonical parent config, omits env-driven TTA, no per-arm threshold
  assertion.

## Assessment (why this is a decision point)
- Core correctness is verified across 11 Codex rounds (byte-parity, fail-closed gate, isolation,
  telemetry, watchdog). All local gates pass (compile, builder parity 31 injected lines strip to
  parent, structural validator, 34-check behavioral test).
- Formal v3 finding #2 is **circular/not locally satisfiable**: it demands verifying the REAL
  postprocessing pipeline's invariance, which requires the GPU run that this review gates. The
  runtime 0.20 byte-parity assert IS real-pipeline evidence (the 0.20 arm must exactly reproduce
  the parent submission on the actual Kaggle pipeline), but the reviewer wants more.
- Finding #3 is completeness polish (canonical-parent ref, TTA env, per-arm threshold assert).

## Formal round 4: REVISE — convergence conclusion

After the round-3 fixes (KeyboardInterrupt watchdog + GPU child reaping; canonical-parent config
comparison + per-arm threshold assertion + env TTA settings; runtime shared-input fingerprint),
Codex ACCEPTED all of: 74-global + env + threshold config checks, control-SHA rejection, metrics
fields, strict telemetry, exact fork/edge deltas, and the KeyboardInterrupt watchdog + child
termination. Remaining objections:
- **(circular, unsatisfiable locally)** "arm-order testing uses a MOCK filter_output_graph; does
  not verify the REAL postprocessing order invariance." Verifying the real postprocessing requires
  the GPU run that this review gates. The runtime 0.20 byte-parity assert + shared-input
  fingerprint ARE real-pipeline evidence, but the reviewer wants a local test of the real function,
  which is impossible without executing on Kaggle.
- (deeper) the input fingerprint hashes path/size/mtime, not graph CONTENTS; heatmap-cache
  immutability not content-verified.
- (doc) some descriptions say "downstream-only replay" while each arm re-runs the FULL
  filter_output_graph (fresh reload per arm) — a wording mismatch to correct.
- (inherent) Python signal handling can be delayed during native computation (not fixable).

**Conclusion:** 4 formal rounds + 5 custom admission rounds + 3 strategy rounds = 12 Codex rounds.
Every fixable item has been fixed and re-confirmed; the standing objection is structurally
CIRCULAR (real-pipeline verification requires the gated GPU run). This reviewer will not reach
PASS on that item. The implementation is verified correct; the residual is verification-depth /
process, not a code-correctness or leakage defect.

## Decision required (user)
The controller launch gate needs review.status == PASSED. Options: (A) keep iterating the formal
review (may not converge on #2); (B) authorize launch despite the formal REVISE, accepting the
documented residuals — either via an explicit governance override of the review gate, or a manual
Kaggle push outside the controller (as repro_059 itself was launched); (C) stop.

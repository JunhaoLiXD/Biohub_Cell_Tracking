# Original-score joint repair integration

User authorization: 2026-09-12 continuation, GPU balance reconciled to 30 hours;
six hours protected. One two-hour remote validation is conditional on fresh
experiment-specific Claude PASS and snapshot smoke. No submission or promotion.

Behavior parent: repro_041_public_0941_motion_ema. Evidence donor: diag_051.
Local discovery: local_052_joint_graph_pilot_v1_attempt02, whose context-increment
hypothesis remains REJECT_LOCAL_POLICY. No parameter change or sweep occurred.

## Exact implementation

Port the original-score solver from the immutable local snapshot. Top k=8,
protected probability=0.9, edit penalty=0.25. Solver functions are copied intact;
the production entry point always selects original_score. No context features
are read by candidate extraction. Existing fork, uncached and high-confidence
edge protections and nonpositive/pure-deletion rejection remain intact.

The shared filter_output_graph function initializes detection provenance on
the raw predicted graph, observes each existing postprocessing stage, and calls
repair only AFTER the unchanged linefit smoothing. Original detection tokens
include detection index and frame; new recovery nodes lack the token, even if
their numeric ID and frame reuse an old value. Removed identities cannot return.
Worker prediction caches are enabled for both test and validation using the
unchanged diag_051 top-eight union accepted-edge export. No scorer or GT data is
passed into repair. All nodes and coordinates are preserved by repair.

## Verification and numerical scope

The first complete upstream smoothing replay on Windows produced exactly the
same edge sets for all 16 videos but coordinate discrepancies up to
1.7053025658242404e-13. Keep this result as BLOCKED_EXACT_COORDINATES in
experiments/local_053_original_score_parity_attempt02/result.json. The initial
single-video assertion stop is retained in local_053_original_score_parity.
This difference occurs before joint repair and is consistent with native
linear-algebra rounding; its platform cause is not independently proven.

The exact NEW-STEP parity check uses each archived no-change graph as the
post-smoothing prediction-only input fixture. Its only fields are predictions,
arm, video and actions; it contains no GT. Provenance eligibility still comes
from the pre-ILP registry and prediction-stage history. Expected repaired output
is opened only after execution. All 16 output node dictionaries and edge sets
match exactly; no-change topology also matches. Result:
experiments/local_053_original_score_final_stage_parity/result.json.

This proves repair-interface parity, not bit-exact cross-platform reproduction
of the upstream pipeline. Remote admission review must assess this distinction.
The remote contract keeps strict canonical input AND repaired graph hashes for
all 16 videos, plus every local score field (absolute tolerance 1e-12), aggregate
0.9535869213120838 and division 4/8/8. No coordinate tolerance was added to remote
graph hashes. Exact rows fix the already declared specimen/panel/worst-video
outcomes; new annotations or post-result thresholds are not introduced.

Thirteen combined tests pass, covering occupied swaps, no-change, order, fork
protection, pure-deletion rejection, identity reuse, context-free cache access,
and actual notebook begin/observe/finish hooks with coordinate preservation.
Snapshot smoke checks syntax, embedded core, hook placement and final gates.

## Solver dependency

The local solver is SciPy 1.18.1. A CPython 3.12 manylinux x86_64 wheel was
downloaded with user-approved network access; wheel and extension SHA256 values
are in .private/runtime/joint_repair_linux/manifest.json. The 25,128-byte _lsap
extension is embedded with its license, hash-verified, loaded under an isolated
module name and assigned only to the new repair module. System SciPy/NumPy are
not replaced, preserving upstream inference and smoothing dependencies.
Before GPU inference, a native-load and occupied-swap assertion runs. Windows
cannot execute this Linux ELF locally; WSL is unavailable. The pinned historical
Kaggle image ran CPython 3.12. Binary compatibility remains a runtime preflight
risk; failed load must stop, without fallback or changing the solver version.

## Limits and decision

Most edited edges are outside annotation support; gains are heterogeneous and
one video regresses. Frozen train16 is not an unseen holdout. The remote run
tests production integration and output validity, not independent generalization.
Report unknown edits using the local audited evidence; do not call them safe.
No external review has occurred when this design is written. Review must inspect
the final immutable notebook/config; do not infer approval from local parity.

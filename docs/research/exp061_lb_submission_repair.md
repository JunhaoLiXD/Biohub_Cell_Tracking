# exp061 submission transport repair

The user reported xyonly-copy scoring failure and authorized diagnosis, submission
repair and one zon resubmission, explicitly prohibiting inference strategy changes.
Both zon-copy and the byte-identical known-good xyonly-copy have no public score;
the screenshot reports a scoring error for xyonly. This strongly supports a static
development-output versus current scoring-input mismatch, not a zon-specific defect.
The exact internal scorer traceback is unavailable. A successful fix still requires
an actual code-competition scoring result.

The existing strategy CONSENSUS is docs/research/exp061_codex_challenge_v5.md.
No new strategy is proposed. The downloaded, previously executed exp061 notebook
is preserved at .private/exp061_lb_repair/upstream. Its inference cells, transforms,
thresholds, frozen configuration, graph writer and three arms remain unchanged.

Two submission adapters are necessary:

1. Replace the development-output fixed hash dependency with an independent
   original-XY replay on the current input, BEFORE installing cached TTA patches.
   The same existing graph writer and pinned tight55 configuration are used.
   The cached xyonly control must exactly match this current-input reference.
   This adds a reference replay, not a prediction-policy change. It retains all
   graph checks and budget checks. The original development hash remains in the
   immutable historical experiment and can be verified on downloaded run output.
2. Require full integrity and completed zon, verify the current-run digest, and
   atomically publish that run's zon CSV at SUBMISSION_PATH. Remove the intermediate
   parent CSV before the replay so failure cannot silently submit the parent.

Validation: source parity and syntax, executable success and integrity/partial/hash
failure controls, fresh experiment-specific Codex review, snapshot smoke, then
one 2-hour-capped run with a 2-hour reservation, retaining six protected GPU hours.
No automatic retry after review timeout/quota stop or remote failure. Do not repeatedly poll.
After completion collect and audit once, compare development zon/xyonly hashes to
2593a5438a17e5649736fcd6ad2f7af4c2fa8f822a759e9f51d877cdf6c840a1 and
d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60 respectively.
Before one authorized LB submission query remote history, enforce the three/day
cap, and record the exact kernel version and submission in SUBMISSION_BUDGET.json.
No baseline promotion or new threshold experiment is authorized.

## Version 2 validation-contract amendment (2026-09-22 UTC)

Codex admission on version 1 returned BLOCK: the changed fixed-hash contract needs
explicit amendment consensus, the reference replay needs executable tests, config
text is stale, watchdog identity must match, and reference timing must be retained.
These objections are preserved in the version 1 experiment's review.md.

Revisions: current-input original-XY parity is explicitly a deployment validation
contract, NOT historical reproduction evidence. Historical xyonly AND zon hashes
remain mandatory post-run/pre-submission development-output checks; neither hash
is imposed on hidden data. All existing algorithm policy, transforms, thresholds,
graph checks and 2h watchdog stay unchanged. Reference timing and dataset costs
are persisted separately. The experiment ID is injected once before execution and
used by watchdog metrics too. Actual replay tests cover original-reference ordering,
intentional reference/control mismatch, reference exception and reference budget
abort, with no parent fallback. The source/config are a NEW immutable v2 experiment.

Inherited exp061 guard-coverage limitations remain disclosed in the v1 review and
original run authorization; this amendment neither hides them nor expands policy.
The user explicitly delegated this repair implementation to GPT-5.6 Sol at medium
reasoning, superseding the default Claude implementation ownership for this bounded
repair only. As implementation owner, Sol agrees with this narrow amendment:
current-input original-XY parity is the deployment gate; both historical development
hashes remain mandatory pre-LB audit evidence; and no inference policy changes are
permitted. Independent Codex concurrence and a fresh experiment-specific admission
PASS remain pending; no new research strategy is proposed.

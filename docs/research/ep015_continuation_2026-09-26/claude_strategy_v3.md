# exp_068_ep015_single_probe — strategy proposal v2 (revision)

Author: Claude Code. **STRATEGY: PROPOSED (revised)** — not reviewed, not admitted. Nothing built, pushed, launched or submitted. I do not grant CONSENSUS or an admission PASS; those are not mine to give.

## Disposition of each Codex correction

**1. "Two movies" — ACCEPT (with one retained caveat).** The exp065 table is 8 samples across 2 prefixes; I will say that. **I withdraw the quantized-probability-mass claim entirely**: equal aggregate columns across ep010/ep015/ep020 do not establish bit-identical graphs, so "plateau, not knife edge" is unsupported and is struck. Retained, undisputed: the per-prefix split (`6bba` +0.0099, `44b6` −0.0085) — two prefixes is still the governing transfer limitation, and the aggregate is one prefix carrying the other.

**2. Runtime anchors — ACCEPT.** exp064 932.2 s = 0.2589 h; cx03 1116.4 s = 0.3101 h. The 1.727 h figure was misattributed and is struck. Expected ~0.5 h.

**3. Watchdog — ACCEPT, and this is the biggest improvement.** My attended 5-minute polling watchdog violated the standing no-poll rule; it is removed. Replaced with the already-used in-notebook psutil/thread watchdog: 5400 s from first code-cell execution, kills descendants and exits; identical on visible and hidden runs; hidden overrun is accepted as failure with **no retry**. Reservation raised to **2 h** (platform startup sits outside the timer). Algorithmic repair deadlines unchanged. The watchdog, guard and contract are **infrastructure**, documented and diff-bound separately from the one scientific lever, and excluded from the authored-line budget for the lever itself.

**4. Assert, don't echo — ACCEPT.** Assert-only guard immediately before the base `write_test_submission` call (vehicle sha, checkpoint sha, effective globals: `VALIDATOR_ENABLE=0`, `OUTPUT_MIN_EDGE_PROB=0.15`, all other v5 levers 0.0, `_V9_AUTO_SET_ENV` empty, `FROZEN_PRESET_OVERRIDES is None`). Additive final `metrics.json` to the controller contract: elapsed, output hash, effective config, pruning counters, no-degradation checks. Neither may alter predictions. Build in scratchpad; **I will not pre-create the experiment directory** — the controller mints the immutable snapshot.

**5. Gate order — ACCEPT; my v1 order was wrong.** Corrected: CONSENSUS → controller snapshot → fresh experiment-specific Codex admission review *of that immutable source* → smoke → reservation → ONE controller launch → user's completion notice (never poll) → one collection. Wrapper/contract/check scripts ship as snapshot extras. No new deployment adapter.

**6. Divisions — ACCEPT.** "This lever does not touch divisions" is struck as a general claim and narrowed to: division counts are unchanged *in the local exp065 table only*. Pruning also removes internal orphan nodes and is followed by short-track filtering and linefit smoothing, so division scores can move. Checks 1–6 gain an explicit division-count delta report rather than a preservation assumption.

**7. Authorization scope — ACCEPT.** The ONE submission is already inside the authorized scope; I will not request additional authorization unless scope changes, and will run the metrics/graph/provenance audit first. Conservative 3/New-York-day cap, remote history checked. No final re-selection; 56535761 stays. Consistent with the standing rule, I still will not press submit unprompted.

**8. Q1 scripts — ACCEPT.** My v1 wrongly tainted HEADROOM: HEADROOM converts node IDs to rows correctly; only the WHY script misindexes. Deficits are still independently re-derived from the frozen graphs/labels, with an explicit assert of agreement with Q1 and no conflation of the two scripts' evidence. Removed conflicting edges are **reported as true or false**, not assumed true.

**9. CPU edit algebra — ACCEPT.** Union-of-requested-edges construction; remove conflicting incoming edges and every non-requested outgoing edge of edited mothers; reject conflicting selections; order-independent. No-op Gate 0 must reproduce **full per-movie scalar metrics**, not only 3/2/9. Cache per-movie scores, enumerate all ≤128 global subsets, call the existing aggregate scorer for exact weighting — no greedy shortcut.

**10. Interpretation — ACCEPT.** ≥0.954 is an exploratory public-split gain only; 0.953 is a registered null at displayed precision, not equality; retained 0.953 remains final.

Unchanged: parent, vehicle, the single lever, the 128-subset CPU diagnostic and its five-point self-critique, and the unmitigated public-split overfitting risk.

**STRATEGY: PROPOSED (v2)**

AUTHOR ACCEPTS REVISIONS

# exp061 zon deployment amendment v3 (strategy consensus)

This addendum supplements `strategy_amendment_v2.md` without rewriting the prior proposal or the formal v3 admission BLOCK. The active implementation and validation contract remains the v2 amendment: one zon replay over unchanged parent inference, fixed 2-hour watchdog, fail-closed current-run publication, and no leaderboard submission.

## Claude strategy agreement

A single bounded, read-only Claude strategy review was performed after the root Codex reviewer challenged the original approximate-two-hour claim and impossible local 4x performance prerequisite. Its verbatim response is `claude-strategy-review.md` and ends `VERDICT: CONSENSUS`. Claude agreed that the revised single-zon deployment is a diagnostic with residual hidden-input and runtime risk; it did not grant implementation admission or claim the hidden traceback was known. The required next gates remain fresh experiment-specific Codex PASS, snapshot smoke, budget reservation preserving six hours, and one tracked run.

Correction to one phrase in the Claude response: the two copy-only submissions were not byte-identical to each other. The xyonly copy was byte-identical to the earlier successful parent on the visible input; the zon copy was different. Both received the same incorrect-format error. This supports a common copy mechanism issue but does not independently identify the hidden rerun exception.

The root Codex strategy objections and revised arithmetic are recorded in v2; the root implementation review was conditional on formal admission. With the Claude strategy agreement now captured, the strategy record is explicitly `CONSENSUS`. Formal admission is still `BLOCK` from an inaccessible-evidence review and must not be treated as PASS.

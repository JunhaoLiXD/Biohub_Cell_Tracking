# Agent Workflow v2

Effective: 2026-09-27

This is the canonical workflow for AI-assisted work in this repository. Its
purpose is to preserve scientific and operational safeguards while avoiding
repeated model reviews, duplicated context, and indiscriminate test runs.

## Risk tiers

Every new task or experiment must declare one tier before substantial work.

### Tier A — maintenance

Use for documentation, state synchronization, log collection, deterministic
formatting, archival work, and small fixes that do not change predictions,
metrics, graph semantics, data access, budgets, or remote execution.

- One agent may implement the work directly.
- No independent model review or strategy-consensus round is required.
- Run only checks selected from the changed paths.
- Remote launches and leaderboard submissions can never be Tier A.

### Tier B — inherited bounded experiment

Use for a single parameter or small localized implementation change on a
verified parent when the validation protocol, data, metric, graph semantics,
and execution vehicle remain unchanged.

- Record one compact experiment card: parent, hypothesis, exact change,
  validation, budget, artifacts, risks, and stop rule.
- The implementing agent may author the card and implementation in one pass.
- Build the immutable snapshot and run deterministic targeted checks first.
- Obtain one independent, experiment-specific implementation/admission review
  before remote launch. A separate strategy-consensus exchange is not required.
- A REVISE response gets at most one delta-only review containing unresolved
  finding IDs, the corrective diff, and new test receipts. It must not resend
  the full historical packet. Further disagreement becomes NO_CONSENSUS and is
  returned to the user.

### Tier C — research or framework change

Use when changing models, objectives, training data or splits, validation or
metrics, graph semantics, leakage boundaries, major decoding behavior, or when
bundling coupled changes.

- Claude authors the strategy and Codex independently challenges it.
- One revision round should normally produce explicit CONSENSUS or
  NO_CONSENSUS. Extra rounds require a concrete new fact, not restatement.
- After implementation, one independent admission review is still required.
- A single delta-only review may resolve implementation findings.

When classification is uncertain, use the higher tier. The user approves major
direction changes and may explicitly raise or lower a task's tier after the
tradeoff is explained.

## Safeguards that always remain

Before every Kaggle remote launch, regardless of tier, require a tracked
hypothesis and parent, exact change, immutable snapshot, targeted smoke PASS,
sufficient GPU budget, leakage protection, output contract, rollback or stop
rule, and a fresh experiment-specific independent PASS. Preserve submission
caps, authenticated remote-history checks, provenance hashes, and the rule that
Public LB evidence does not automatically promote a final candidate.

## Bounded review packets

For Tier B, the normal review packet should be at most 15 KB of text and contain:

1. the experiment card;
2. the snapshot config;
3. a parent-to-candidate diff or changed-cell extract;
4. concise targeted-test receipts;
5. budget and provenance summaries with paths and hashes.

Do not embed complete notebooks, historical logs, prior prompts, or entire
handoff files. Reviewers may open a named source only to resolve a concrete
uncertainty. Revision packets contain only unresolved findings and deltas.

Tier C packets may be larger when necessary, but should still reference hashed
artifacts instead of copying them. Prompts and responses are evidence, not input
to every later review.

## Context and memory

At session start read `STATE.json`, the active experiment record, and
`.private/current/CONTINUATION.md`. Read `GOAL.md`, `MEMORY.md`, historical plans,
or archived experiments only when a concrete question requires them. `STATE.json`
is the sole current-state authority; do not duplicate long current summaries
across multiple files.

Continuation notes must be concise: current state, completed evidence, next
action, blockers, and authorization boundaries. Historical narrative belongs in
versioned research documents or archives.

## Test selection

Select tests by changed path and risk:

- documentation/state only: checkpoint rendering and format checks;
- controller changes: controller tests;
- experiment module changes: that module's unit tests and snapshot smoke;
- notebook builder changes: deterministic rebuild, syntax, hash, and contract
  checks;
- full maintained `tests/`: milestones, releases, or broad controller changes.

Never use unrestricted pytest discovery across archived experiment snapshots.
Write long command output to an artifact and report only the exit code, failing
test names, and a short tail. Do not send large successful logs to a model.

## Model allowance

Use deterministic scripts for hashes, schemas, configuration equality, graph
invariants, budget arithmetic, and test selection. Use models for scientific
judgment and code review. Prefer one bounded call over iterative conversation,
and never retry a timeout or quota failure automatically. Tier A uses no model
review; Tier B uses one reviewer call plus at most one delta review; Tier C uses
the bounded strategy and implementation reviews described above.

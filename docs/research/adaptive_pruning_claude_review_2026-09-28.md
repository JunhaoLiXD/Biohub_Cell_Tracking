# Claude strategy review - adaptive protected pruning

Date: 2026-09-28

## Initial verdict

`REVISE`

Claude found the scientific direction, scorer alignment and feasibility adequate.
Its blocking concern was selection bias from screening three policies on the same
eight held-out movies and advancing the best.

## Required changes

1. Pre-register `fork_protected_ep015` as the only promotable primary; treat the
   other policies as confirmatory diagnostics only.
2. Require nested leave-one-movie-out evaluation, including positive sign with
   movie 44b6 omitted.
3. Preserve every individually credited fork; net-zero fork count is insufficient.
4. Apply dispersion gates before reading the pooled delta.
5. Budget one LB slot only if the primary passes every gate; otherwise close the
   arc with zero GPU and zero submissions.

These changes were incorporated into `PLAN.md`. One delta-only review follows.

## Delta response and Codex challenge

Claude declined to issue a second reviewer verdict because the Tier C workflow
assigns strategy authorship to Claude and independent challenge to Codex. It also
raised one substantive residual risk: confirmatory results computed on the same
eight movies could be visible when the primary decision is made.

Codex independently accepted that finding. `PLAN.md` now requires the primary
metrics and terminal disposition to be written to an immutable receipt before any
confirmatory arm is computed. The disposition cannot later be reopened or changed.
This removes the remaining selection channel while retaining the confirmatory arms
only for explanation and possible future, separately governed research.

`VERDICT: CONSENSUS`

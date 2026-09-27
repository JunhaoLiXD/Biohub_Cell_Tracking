# Independent strategic judgement — Codex, 2026-09-25

Reviewer: Codex `gpt-6-astra`, effort low, read-only. Asked for an INDEPENDENT ranked plan from a
purely factual brief. **Claude Code's own ranking was deliberately withheld from the prompt** so the
judgement would not be anchored; the brief carried measurements, budget, deadline and the public
landscape only.

**Codex's verdict: continue, with a small bounded portfolio — not four days of tuning.** Order:
`cx03` probe, then an `ep015` probe, then an event-led division audit with at most two targeted
interventions, then the V1284-removal A/B, then a timeboxed inspection of the three unanalysed public
artifacts. ~7 GPU h and <=5 slots total, stop new research 2026-09-28.

**Claude Code's verification: three of its factual criticisms of my analysis are GENUINE and material.
They are recorded at the end of this file. Codex's plan is better founded than the choice set I gave
the user, which omitted `cx03` entirely.**

---

**I would continue, but with a small, bounded portfolio—not spend four days exhaustively tuning.** My first submission would be `cx03`, followed by one `ep015` probe. My main research effort would be a division-error audit leading to at most two targeted interventions. I would stop new research on September 28 and preserve the remaining time for final selection and deployment reliability.

I would not treat “stop or force ep015” as the complete choice set. `cx03` deserves consideration, and the division bottleneck remains largely untested.

I inspected the current handoff, exp_065 record, archived vehicle source, and sweep results. The costs below are planning estimates, not measured runtimes for new experiments. I use your stated five-submission daily cap; the plan needs no more than three on any day.

**Ranked by expected value relative to cost**

| Priority | Action and mechanism | GPU budget | LB slots | Evidence required / stopping rule |
|---|---|---:|---:|---|
| 1 | **Probe `cx03` alone.** Reduce excess predicted nodes with relatively little embryo-specific damage. | ~0.3–0.5 h | 1 | Prove the active setting changes the final output. Submit once; no neighboring threshold search. |
| 2 | **Probe `ep015` alone.** Larger measured count-adjustment gain, substantially greater distribution sensitivity. | ~0.3–0.5 h | 1 | Same runtime proof. Treat this explicitly as a speculative exception to the rejected gate. |
| 3 | **Audit division failures, then test at most two targeted mechanisms.** Recover actual missed events or remove false events. | Up to 4 h | 0–2 | Continue only if event-level evidence identifies reachable errors and candidate changes survive into the final graph. |
| 4 | **Remove V1284 from x138 in a matched A/B.** Test whether coordinate refinement damages matching or association. | Up to 2 h | 0–1 | Require changed coordinates/graphs and a favorable full-metric comparison beyond the discovery movies. |
| 5 | **Inspect the three unanalysed public artifacts.** Look for a genuinely different, usable mechanism or pretrained signal. | 0 h for inspection; no automatic launch | 0 | Timebox to two hours of analysis. An unusually compelling finding may replace priority 4. |

That commits at most about **7 GPU hours and five submissions**, leaving over ten hours for confirmation, execution problems, or simply unused. Available slots are not a target to fill.

### Why `cx03` comes first

Its expected gain is smaller than ep015’s, but its worst prefix loss is roughly **53 times smaller**. For an unrevealed private distribution, that is a meaningful distinction.

There is also an important detail in the actual sweep CSV: `cx03` improves the notebook’s original aggregate by **0.00090086**, just below its **0.001** selection margin. Its test-reweighted gain is **0.00115**. Thus, “the notebook selected base” does not mean this candidate demonstrated no useful effect; it narrowly missed one aggregate cutoff and failed your stricter admission criteria.

I would preserve those rejection records and register a separate exploratory probe. I would not retroactively declare it a passing experiment.

For ep015, **+0.00236 for roughly 0.3 hours and one slot is worth testing**, even with the substantial prefix regression. However, 10 losing subsets out of 36 is neither a calibrated failure probability nor evidence of a literal coin flip: those subsets overlap and come from only eight movies.

I would not immediately combine the two. There is no evidence yet that a combination adds value.

### The division investigation should be event-led

The project has spent considerable effort on downstream interventions that repeatedly leave divisions unchanged. Meanwhile, nine missed divisions remain unexplained at the level needed to choose an intervention.

For each of the 12 labelled events, I would establish:

- Whether the parent and both daughters exist among predicted detections.
- Whether the correct candidate links are generated.
- Which gate rejects them, including the actual scores and geometry.
- Whether accepted links survive solving and all subsequent processing.
- Whether the final scorer recognizes the correct parent–daughter identities.

The two false positives need the same tracing. Ground truth may diagnose failures; it must not become a movie-specific inference rule.

The vehicle already contains `division_recoverability_audit()`, but **its shortcut is insufficient**: it labels a matched parent with two outgoing edges “reproduced_ok” without checking that those edges reach the correct daughters. I would reconcile the audit against the actual division scorer before trusting its conclusions.

Then choose at most two changes:

- If correct candidates are specifically blocked by DeepCenter, test a substantial, fixed veto relaxation such as `dcsd010`.
- If correct candidates fail divergence, test `diverge150`.
- If the second daughter exists but never acquires the right connection, test one second-daughter repair configuration.
- If the required detections are missing, abandon this post-processing route. Do not spend the remaining days relaxing irrelevant gates.

The funnel’s high rejection percentages alone tell us nothing about whether it rejects true divisions. Most rejected candidates may be correctly rejected negatives.

I would require improvement in the **complete metric**, with changed-event identities and edge damage reported. Recovering three FN while holding everything else fixed gives your stated +0.02143 locally, but that is conditional arithmetic—not a forecast of leaderboard gain.

### Your validation evidence is weaker—and less exhausted—than it appears

Two source findings matter:

**The selector does not choose the division-richest movies.** It sorts by “contains any division,” then lexicographically by stem. Consequently, the observed twelve events do not establish that increasing the sample cannot expose more division events.

**The edge aggregate uses `TP + FP + FN` weights**, which can change with the candidate. Reweighting by test node shares is a useful sensitivity analysis, but it is not automatically the same aggregation as the official hidden score.

I would therefore evaluate any division finalist on additional, previously uninspected movies, selected in advance across prefixes and including movies without labelled divisions. Those negatives are necessary to measure the cost of relaxing division gates. Where checkpoint training provenance prevents a truly untouched validation set, call it a confirmation panel rather than independent held-out evidence.

The older **+0.01485 local repair gain that produced no public improvement** is particularly relevant. It argues against another large local search followed by a single triumphant submission.

### What I would deprioritize

- **Another pruning sweep:** the relevant alternatives have already been measured. Two fixed probes are enough.
- **Blind sweeps of all remaining named knobs:** choose settings from observed error paths, not suggestive names.
- **Z-reflection TTA deployment repair:** scientifically unresolved, but five deployment failures make it unattractive this late unless the working x138 vehicle makes integration demonstrably trivial.
- **New detector training or a framework rewrite:** insufficient time for discovery, validation, and reliable hidden execution.
- **More public-notebook ladder chasing:** inspect the unusual artifacts once, then stop. Author scores do not establish notebook scores.
- **`seyitkaangunes` as a wholesale replacement:** it removes many settings simultaneously, and leaf pruning already looks weak.
- **Immediate DivNet adoption:** it may help reject false divisions, but a verifier may also worsen recall. Check training provenance, input compatibility, and actual runtime activation first.

V1284 removal is a cleaner experiment than most remaining alternatives: one isolated component, no new checkpoint, and a plausible route to change matching. It ranks below division diagnosis because its expected direction is currently unknown.

### How I would decide with no private score

**No experiment before close can establish private success.** Public improvement is useful transfer evidence, not proof. My final choice would weigh public score, additional-movie results, prefix sensitivity, changed-event evidence, and execution reliability.

A public-flat result closes that branch operationally; it does not prove numerical equality when scores are rounded. A public improvement from ep015 would not automatically outweigh its large prefix regression for final selection.

If the rules allow multiple final selections, I would retain x138 alongside the strongest supported challenger. I would verify that rule before relying on it. The public rules page did not expose readable details in this session.

Finally, identical visible CSV bytes do **not guarantee identical hidden-rerun behavior** between different notebook sources. The record overstates that implication. Avoiding a redundant submission was sensible, but preserve the exact successfully scored x138 notebook and dependencies as the fallback.

**My stopping point is explicit:** after the two cheap probes, abandon division work if the audit cannot identify actionable true-event failures within its budget. If no challenger survives confirmation, stop and keep x138. Protecting 0.953 is sensible; concluding today that all remaining research has negative expected value is not supported by the evidence.

---

## Claude Code's verification of Codex's criticisms (2026-09-25)

Three are material and all three are **genuine**. Each was re-derived from our own run's artifacts.

### 1. I omitted `cx03` from the choice set entirely — CONFIRMED, and it is the safer candidate

| | notebook aggregate delta | vs its 0.001 margin | worst prefix regression | vs the author's −0.0005 cap |
|---|---|---|---|---|
| `cx03` | **+0.00090086** | misses by 0.0001 | **−0.00016144** | **PASSES** |
| `ep015` | +0.00512577 | clears | **−0.00849388** | **fails** |

`ep015`'s worst per-embryo regression is **52.6× larger** than `cx03`'s. So the notebook selecting
"base" does **not** mean `cx03` showed no effect — it narrowly missed one aggregate cutoff while being
the only candidate that satisfies the author's own anti-overfit cap. My Gate 2 excluded it on my own
`+0.0015` aggregate bar (`cx03` is +0.00115 test-reweighted), and I then presented the user a choice
between "stop" and "force `ep015`" without mentioning it. That was a real gap.

### 2. My claim that the 8 held-out stems are the "division-richest" available — WRONG

The selector is `ranked = sorted(stems, key=lambda s: (not division_flags[s], s))` and
`_stem_has_gt_division` returns a **boolean** (`any(out_degree >= 2)`). So it sorts by *contains any
division*, then **lexicographically by stem name** — not by division count. **Twelve GT events is
therefore not a ceiling**, and raising `BIOHUB_VALIDATOR_N_PER_TYPE` could expose more. My statement
in `STATE.json` that these "ARE the division-richest held-out movies available" is withdrawn, and with
it the strength of my "division work is essentially unmeasurable" conclusion.

### 3. A `division_recoverability_audit()` already ran and I never read its output — CONFIRMED

It is in our own log. **This is the most decision-relevant number we have and it sat unread:**

```
TOTAL: reproduced_ok=2  recoverable_by_postprocess=7  missing_second_daughter=3  parent_unmatched=0
recoverable -> try dcsd010/dcsd015/divwide/sym075/diverge150 family
             + v5 second-daughter repair (repd010/repd015/repd015w)
missing     -> detection-limited; post-processing cannot recover these
```

**7 of the division FNs have both GT daughters already matched to predicted nodes** — the detections
exist and only the linking is missing — against only **3** that are detection-limited. That
contradicts the framing I gave the user, that division recall is upstream-locked. Recovering 3 of
those 7 is worth **+0.02143** proxy.

Two caveats, one of which is Codex's and correct:

- Codex is right that the audit's `reproduced_ok` branch is unsound: line 5649 counts a matched parent
  with ≥2 outgoing edges as reproduced **without checking those edges reach the correct daughters**.
- Concrete evidence of exactly that: the audit reports `reproduced_ok=2` while the official division
  scorer reports `div_tp=3` on the same base config. **The two disagree by one event**, so the audit
  must be reconciled against the scorer before its counts are trusted.

### 4. A cost of my own design choice that I did not flag

I narrowed the exp_065 sweep from 41 candidates to the 15-member pruning family, on cost and
multiplicity grounds. That decision **excluded precisely the division family this audit points at** —
`dcsd010`, `diverge150`, `divgap60/70`, `repd010`, `repd015`, `repd015w` were never scored. Of the
named family only the ones already in the archive were measured, and those were mostly harmful
(`sym075` −0.0054 proxy, `repd_divgap` −0.0066, `dcsd015` +0.0018, `divwide` ≈ 0). The untested ones
remain untested.

### 5. Where I agree with Codex against my own earlier wording

- "Coin flip" for `ep015` overstated it. 10 of 36 **overlapping** subsets drawn from 8 movies is a
  fragility indicator, not a calibrated loss probability.
- Byte-identical visible CSVs do **not** guarantee identical hidden-rerun behaviour between two
  different notebook sources. Gate 1's PASS is evidence about the visible run; the exact x138 notebook
  that actually scored 0.953 should be preserved as the fallback regardless.
- DivNet caution matches my own finding independently: it is a veto, so it addresses `div_fp = 2` and
  cannot touch `div_fn = 9`.

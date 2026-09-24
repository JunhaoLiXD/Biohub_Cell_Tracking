# exp_063 Codex challenge v1 — verdict REVISE

Reviewer: Codex `gpt-6-astra`, effort low, read-only, 2026-09-24. Target:
`docs/research/exp063_next_step_proposal_v1.md`. Response: `exp063_next_step_proposal_v2.md`.

> **Evidence-access caveat, recorded:** this run hit the known
> `helper_unknown_error: setup refresh had errors` tool failure partway through, so Codex could not
> independently recompute the notebook-overlap figures or fully read `STATE.json` /
> `SUBMISSION_BUDGET.json`. Its findings are therefore **reasoning-level**, which is where they
> land anyway. Claude Code verified the two load-bearing factual points afterwards: the protected
> 6.0 h reserve (confirmed, v1 was wrong) and the `tight55` freeze (confirmed, v1 was wrong).

---

**A bounded whole-pipeline reproduction is defensible. Permanently abandoning porting on the evidence in v1 is not.** The proposal turns weak evidence into categorical conclusions, understates the audit burden, and has an incomplete budget and decision rule.

Evidence limitation: the initial bulk read was truncated, and subsequent shell calls failed with `helper_unknown_error: setup refresh had errors`. I read the proposal, recon and HANDOUT, plus the returned contract and budget excerpts. I could not independently recompute notebook overlap or fully inspect `STATE.json` and `SUBMISSION_BUDGET.json`. The overlap numbers, current 403 and new notebook’s compliance scan therefore remain **proposal-reported**, not independently verified.

1. **The recon overclaimed portability. The proposal overclaims its refutation.**

   The recon explicitly derives “our exact 0.947 base” and “directly portable” from a shared provenance header. That is insufficient: ancestry does not establish an identical effective pipeline. The proposal is right to challenge that inference. [Recon:71](E:/Project/Biohub_CellTracking/docs/research/public_frontier_recon_2026-09-23.md:71)

   But **35.7% textual overlap does not establish “a pipeline ~64% different.”** Line-set similarity ignores execution, duplicated lines, formatting, comments, generated scripts and inactive branches. A notebook can remove extensive diagnostics while retaining the same predictor; one changed assignment can produce different predictions despite 99% overlap. [Proposal:26](E:/Project/Biohub_CellTracking/docs/research/exp063_next_step_proposal_v1.md:26)

   The measurements also need a defined denominator. A set-based percentage cannot automatically support “2850 parent lines absent” as a count of line occurrences. Different notebook hashes establish different bytes, not substantively different inference.

   Likewise, `PPSWEEP` falling from 14 occurrences to 2 and lowercase `ppsweep` disappearing **does not prove loss of tight55 behavior**. The other notebook could freeze the selected parameters directly. Marker counts establish neither execution nor parameter equivalence. [Proposal:32](E:/Project/Biohub_CellTracking/docs/research/exp063_next_step_proposal_v1.md:32)

   **What would change my mind:** comparison of effective configuration, executed prediction/post-processing paths, model inputs and weights, and where each proposed lever enters those paths. Until then, the correct finding is: **exact-base portability was not established; incompatibility has not been established either.**

2. **The 0/4 versus 1/1 argument is not a usable base rate.**

   exp_061 never scored. It is a delivery failure, not a measured accuracy failure. HANDOUT explicitly calls zon “UNRESOLVED, not falsified.” The proposal cannot quietly turn missing outcomes into zero improvements. [HANDOUT:172](E:/Project/Biohub_CellTracking/HANDOUT.md:172)

   The remaining interventions are not exchangeable trials: different parents, different mechanisms, different validation evidence. exp_055 had a genuine proxy-to-LB transfer failure; exp_057 skipped proxy scoring. [HANDOUT:203](E:/Project/Biohub_CellTracking/HANDOUT.md:203)

   Nor was repro_059 an arbitrary public pipeline sampled from the same population as today’s unverified headline. Its success demonstrates that **one particular adoption worked**. It does not estimate the success probability of copying another author’s notebook.

   “The only thing that has ever moved our score” is also broader than the evidence presented, which covers selected recent experiments. [Proposal:68](E:/Project/Biohub_CellTracking/docs/research/exp063_next_step_proposal_v1.md:68)

   There is a respectable argument here: **a bounded reproduction might deliver more information per remaining day than another integration-heavy experiment.** That argument needs credible audit and runtime costs. Dressing it up as 0/4 versus 1/1 makes it weaker.

3. **Answers to the proposal’s six questions.**

   **Q1 — Justified pivot or results-chasing?**  
   As written, results-chasing with a plausible operational rationale underneath. An unverified 0.951 title is a hypothesis, not evidence of expected improvement. Absence from the top 200 weakens corroboration but does not prove dishonesty; account names and team identities need not match. Vote counts add essentially no accuracy evidence.

   I would support one bounded candidate evaluation after its executable provenance and costs are established. I do not support declaring the entire porting approach exhausted.

   **Q2 — Minimum acceptable audit?**  
   “We authored nothing” is not a safety or reproducibility argument. You inherit every upstream defect. The proposal’s exemption from behavioral testing is particularly unjustified after HANDOUT documents inherited cache and telemetry hazards. [Proposal:75](E:/Project/Biohub_CellTracking/docs/research/exp063_next_step_proposal_v1.md:75), [HANDOUT:138](E:/Project/Biohub_CellTracking/HANDOUT.md:138)

   Minimum evidence must cover:

   - Frozen notebook version/hash, dependency environment, mounted dataset versions and checkpoint hashes.
   - Executed code, including imported or unpacked code—not just notebook text.
   - Origins and training-data provenance of the added DivNet weights.
   - Actual prediction paths, cache/fallback behavior, GT use and specimen-specific branching.
   - Output schema, graph integrity, hidden-rerun compatibility and measured resource consumption.

   Patch-specific parity and anchor tests may be unnecessary for a genuine copy. **Output and execution validation remain necessary.** If there is insufficient time for that minimum, do not run it.

   **Q3 — What does the 403 mean?**  
   Less reproducibility, not proof of misconduct. “Made private or deleted” is not established by a 403 alone. Also, the recon says the notebooks were “all pulled and inspected”; inability to fetch again does not establish that no local archived copy exists. [Recon:36](E:/Project/Biohub_CellTracking/docs/research/public_frontier_recon_2026-09-23.md:36), [Proposal:52](E:/Project/Biohub_CellTracking/docs/research/exp063_next_step_proposal_v1.md:52)

   An archived artifact with acquisition metadata and hash would resolve much of this concern. Without one, quoted code remains documentary evidence, not a reproducible source artifact.

   **Q4 — Does dropping PPSWEEP matter?**  
   Potentially, but the proposal has not established what behavior was dropped. Separate the sweep machinery from its selected policy.

   More importantly, the decision table is logically wrong: A scoring ≤0.946 would show that **our frozen reproduction under our execution conditions underperformed**. It would not falsify every haideptry mechanism or prove the historical 0.951 claim false. A score of 0.947 would not establish “relabelling” either; rounded aggregate equality is not prediction equality. [Proposal:102](E:/Project/Biohub_CellTracking/docs/research/exp063_next_step_proposal_v1.md:102)

   **Q5 — Can attribution be sacrificed?**  
   Yes. A reproducible, compliant whole-pipeline improvement can be useful without component attribution. That was already the nature of repro_059.

   What cannot be sacrificed is knowing **which artifact produced the result, from which inputs, through which execution path**. “A number and no understanding” is acceptable only in the narrow sense of unresolved causal attribution—not unresolved leakage or execution provenance. Also, Public LB improvement does not establish private-set improvement.

   **Q6 — Should exp_062 gate this?**  
   It should gate the incumbent comparison and expenditure decision. It need not prevent read-only source assessment.

   If k2 scores 0.949 or 0.950, A scoring 0.948 must not replace it merely because A beats the stale 0.947 comparator. The active decision rule already promotes k2 at ≥0.948. [HANDOUT:39](E:/Project/Biohub_CellTracking/HANDOUT.md:39)

   Waiting for an already-running experiment’s result has high information value and little additional experimental cost. Permanently closing its research line before seeing that result is premature.

4. **Budget, reproducibility and authorization defects that prevent execution approval.**

   - **Protected reserve omitted.** Available discretionary GPU is approximately **18.671187 − 1.75 − 6 = 10.921187 hours**, not 16.9 hours. A small reproduction may fit, but “roughly nine runs” spends protected capacity. [GPU ledger:355](E:/Project/Biohub_CellTracking/GPU_BUDGET.json:355), [GOAL:43](E:/Project/Biohub_CellTracking/GOAL.md:43)
   - **Runtime comparison is not matched.** The 1.727487-hour measurement is exp_062’s control kernel; HANDOUT separately reports 543.08 seconds of measured inference. Comparing that entire kernel with a notebook title’s “19m” does not establish fivefold throughput. [HANDOUT:54](E:/Project/Biohub_CellTracking/HANDOUT.md:54)
   - **“1.1 h worst case” is an estimate, not a ceiling.** It excludes the stated second hidden-rerun attempt and later tuning. “At most two submissions” likewise does not describe the complete proposed schedule. [Proposal:111](E:/Project/Biohub_CellTracking/docs/research/exp063_next_step_proposal_v1.md:111), [Proposal:126](E:/Project/Biohub_CellTracking/docs/research/exp063_next_step_proposal_v1.md:126)
   - **The leakage pre-check is insufficient.** Absence of four names and network calls cannot establish checkpoint cleanliness, absence of encoded lookup behavior, or provenance of bundled code/data. Public availability of DivNet establishes accessibility, not permitted training provenance. No actual leakage is demonstrated here; neither is adequate clearance. [Proposal:56](E:/Project/Biohub_CellTracking/docs/research/exp063_next_step_proposal_v1.md:56)
   - **Missing bounded follow-up policy.** “Inconclusive,” “mapping the family,” and “tune inside whichever pipeline wins” leave experiment count and stopping conditions open.
   - **Gates remain mandatory.** Strategy consensus, major-direction authorization, fresh experiment-specific admission PASS, smoke, reservation and independent artifact audit remain required. Each LB submission still needs user authorization and a remote cap check. The proposal’s initial disclaimer is correct; its schedule does not supply authorization. [AGENTS:28](E:/Project/Biohub_CellTracking/AGENTS.md:28), [AGENTS:86](E:/Project/Biohub_CellTracking/AGENTS.md:86), [AGENTS:107](E:/Project/Biohub_CellTracking/AGENTS.md:107)

   Finally, **0.949 does not guarantee re-entry into the top 200**: the cited cutoff is dated, rounded and potentially tied.

5. **The better choice.**

   **Choose (b) now: finish the authorized exp_062 evaluation.** Then compare a bounded whole-pipeline reproduction against the actual incumbent.

   I provisionally prefer **one audited reproduction** over immediately committing to another expensive port, because it tests the complete claimed package and avoids integration work. That preference is conditional on provenance and cost—not the 0/4 story.

   Density-adaptive porting remains a legitimate alternative if its effective delta is small and inspectable, or the public package cannot clear audit. Doing nothing and retaining the best authenticated candidate is preferable to another unbounded transport or tuning arc.

   Required changes to the reasoning and execution terms are:

   - Replace text-overlap and base-rate claims with appropriately limited conclusions.
   - Establish frozen executable provenance and the minimum audit evidence.
   - Condition comparison and promotion on exp_062’s actual result.
   - Account for protected GPU, retries and all proposed submissions.
   - Bound B, retries and tuning; stop treating one result as a verdict on an entire family.
   - Preserve all independent admission and authorization gates.

**VERDICT: REVISE**

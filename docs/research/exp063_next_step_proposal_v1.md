# exp_063 next-step strategy — proposal v1 (Claude Code)

Status: **PROPOSAL, awaiting Codex challenge.** No experiment, launch or submission is authorized
by this document. Parent remains `repro_059` = Public LB **0.947** (submission 56313491).

Date: 2026-09-24. Deadline: **2026-09-29 23:59** (5 days). GPU remaining **18.671 h**
(1.75 h reserved for the running exp_062 k2). Submission cap **3 / America-New_York day**
(project rule, stricter than the platform's 5), **0 used today**.

---

## 1. Two findings that change the picture, both established today

### 1.1 The recon's central portability claim does not survive measurement

`docs/research/public_frontier_recon_2026-09-23.md` section 3 states the three public levers "sit
on **our exact 0.947 base**" and are "**directly portable** to our parent rather than requiring a
base change." That conclusion was drawn from the notebooks' **self-reported provenance header**
(`source_kernel: raykkretzschmar/biohub-bidirectional-primary-union13-diagnostic-v1`,
`source_notebook_sha256: 3e65ca69...`), which does match.

Measured against the actual code, it is wrong. Diffing each public notebook against our parent
`experiments/repro_059_public_0947_exact_copy/snapshot/source/biohub-repro059-public-0947-exact-copy.ipynb`
(4199 lines):

| notebook | lines | difflib ratio | line-set Jaccard | **% of our parent's lines present** |
|---|---|---|---|---|
| `haideptry/biohub-0-951-sota-deepcenter-fast-ilp-19m` | 3803 | 0.337 | 0.219 | **35.7 %** |
| `haideptry/biohub-sota-0-948-density-adaptive-2xt4-22m` | 3726 | 0.340 | 0.221 | **35.7 %** |
| `haideptry/biohub-0-948-sota-density-rank-2xt4-fast` | 3796 | 0.338 | — | 35.7 % |

Roughly **2850 of our parent's lines are absent** and ~2450 new lines are present. Marker counts
show this is substantive, not cosmetic: `PPSWEEP` 14 -> 2 and `ppsweep` 5 -> **0** (they dropped
the adaptive post-processing sweep our parent depends on, whose `tight55` selection is part of our
0.947), `EDGE_FEATURE_TTA` 17 -> 6, `DEEPCENTER` 97 -> 80, `SAFE_DIV` 70 -> 55, while `DIVNET`
0 -> 9 and `density` 19 -> 28.

Our parent's own pulled SHA is `5b349d3c...`, **not** rayk's `3e65ca69...`. So our parent and
haideptry's notebooks are **diverged cousins of a common ancestor**, not base-and-patch. The
shared header attests ancestry, not code proximity.

**Consequence.** "Port lever X onto our parent" is not extraction of a known-good delta; it is
hand-reimplementation of a mechanism into a pipeline ~64 % different from the one the claim was
measured on — with the sweep that mechanism may interact with *removed* on their side. That is
exactly what exp_062 is doing right now, and it is a materially weaker inference than the recon
presented.

### 1.2 Two facts about the public frontier have moved since 09-23

- **`haideptry/biohub-0-951-sota-deepcenter-fast-ilp-19m` exists** (published 09-21, 7 votes) and
  the 09-23 recon does not mention it. It claims **0.951** — above the rank-200 cutoff of 0.949.
- **`haideptry/biohub-sota-0-948-mutual-best-density-2xt4`** — the combined notebook the recon used
  as its primary evidence for lever 1 — now returns **403 Forbidden**. It has been made private or
  deleted. We can no longer re-read the artifact the recon's lever-1 code block was quoted from.

Compliance pre-check on the 0.951 notebook (ours, run today, not the author's attestation): all
four hidden-test dataset names (`44b6_0113de3b`, `44b6_0b24845f`, `6bba_05b6850b`,
`6bba_05db0fb1`) appear **zero** times, in full or by stem; test discovery is dynamic
(`TEST_DIR`/`iterdir`/`glob`); no `solution.csv` or `sample_submission` read; no network
(`enable_internet: false`, no `requests`/`urlopen`). Dataset sources are **the same three Pilkwang
checkpoints we already mount** plus `giorgosi/biohub-divnet-v2` (5.2 MB, public). Nothing blocks
mounting it.

---

## 2. The strategic read

Our record on **porting a mechanism onto our parent** is **0 for 4** at 3-decimal LB resolution
(exp_055 0.942, exp_057 0.944, exp_060 0.947, exp_061 never scored). exp_062 is the fifth attempt,
and our own strategy record already calls a null "genuinely likely."

Our record on **adopting a whole public pipeline verbatim** is **1 for 1, and it is the only thing
that has ever moved our score**: `repro_059` took us 0.944 -> **0.947 (+0.003)**.

With 5 days left the binding constraint is **not** GPU (16.9 h free, roughly 9 runs) and **not**
submissions (3/day x 5 = 15). It is the **proposal -> challenge -> build -> admission -> smoke**
cycle, which for exp_062 consumed several days and three substantive review rounds. We can afford
perhaps **one** more experiment of that weight — or **several** repro-shaped runs, which need no
hand-written patch, no parity guard, no anchor-uniqueness proof and no behavioral test suite,
because nothing is being modified.

The 0.951 notebook also claims a **19-minute** runtime against our parent's **1.73 h measured**. If
true, each probe costs ~0.3 GPU h instead of 1.73 — roughly **5x more probes per hour**.

## 3. Proposal

**Pivot from "port a lever onto our parent" to "reproduce a whole public pipeline", and keep
exp_062 as the last of the porting line.**

Concretely, as `exp_063_public_pipeline_repro`, repro-shaped (verbatim copy, zero code authored by
us — the `repro_059` playbook):

| arm | notebook | claim | cost |
|---|---|---|---|
| **A** | `haideptry/biohub-0-951-sota-deepcenter-fast-ilp-19m` | 0.951 | ~0.3-0.5 h |
| **B** | `haideptry/biohub-sota-0-948-density-adaptive-2xt4-22m` | 0.948 | ~0.4-0.6 h |

Run A first. Submit A. Run B only if A is inconclusive, or if A's score justifies mapping the
family. Both are single-config notebooks whose own `submission.csv` *is* the arm — the transport
shape that has actually scored (exp_060 56361673, and repro_059 itself).

Decision rule vs 0.947, on **authenticated** submission history only:

| A's Public LB | action |
|---|---|
| **>= 0.949** | adopt as the new parent; we re-enter the top 200; spend remaining days on B and on tuning *inside* that pipeline |
| **0.948** | real but small gain; adopt, then run B |
| **== 0.947** | the family is a relabelling of our own operating point; run B once, then stop |
| **<= 0.946** | the "0.951" claim is false; **abandon the haideptry family** and stop chasing public levers |

**Stop rule.** If A errors in the hidden rerun (the exp_061 failure mode) **twice**, abandon the
route — do not build a third transport. If A and B both score <= 0.947, accept 0.947 as final and
spend no further GPU.

### What this does NOT claim

- It does **not** claim 0.951 is real. The author is absent from the top 200 (cutoff 0.949) and the
  notebook has 7 votes. The number is a **hypothesis worth exactly one submission**, and the
  submission is the test.
- It gives **no causal attribution**. If A scores above 0.947 we will not know which of its ~2450
  new lines did it. Five days out I judge score > attribution; I flag this as a deliberate trade,
  not an oversight.
- It is **not** a claim that exp_062 was wasted. exp_062's control proved its insertion inert and
  its k2 is already running at no extra cost.

### Budget and timeline

| day | action |
|---|---|
| 09-24 | exp_062 k2 completes -> collect; submit only if it differs from control. Stage exp_063 A (a copy — no authored code). |
| 09-25 | Codex admission on the repro record -> run A -> submit A |
| 09-26 | collect A; if warranted run B -> submit B |
| 09-27 to 09-28 | tune inside whichever pipeline wins; buffer for a transport failure |
| 09-29 | final submission, deadline 23:59 |

GPU: A + B about 1.1 h worst case against 16.9 h free. Submissions: at most 2 of the 15 available.

## 4. Risks I want Codex to attack

1. **Is the pivot justified, or is it results-chasing?** The 0/4-vs-1/1 comparison has n = 5 and the
   1/1 is a single event. Argue the other side.
2. **Unaudited third-party code.** We would run ~2450 lines we did not write and cannot fully audit
   in the time available. `repro_059` set that precedent, but precedent is not justification. What
   is the minimum audit that makes this acceptable?
3. **The 403.** A notebook central to the recon disappeared. Does an author withdrawing artifacts
   change how much weight their remaining claims deserve?
4. **Does dropping PPSWEEP matter?** Their pipeline removes the adaptive sweep that selected our
   `tight55`. If our 0.947 partly depends on it, arm A may score *below* 0.947 for a reason
   unrelated to the levers — and we would misread that as falsifying the family.
5. **Am I wrong that attribution can be sacrificed?** If A scores 0.950 with no attribution, we have
   a number and no understanding, four days from the close, and no way to defend it.
6. **Should exp_062 k2's result gate this at all?** I propose it should not. Challenge that.

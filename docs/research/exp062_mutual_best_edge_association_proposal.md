# exp_062 — Mutual-best edge association on the frozen 0.947 pipeline

Status: **v1 — SUPERSEDED. Codex challenge v1 returned REVISE** with 4 CORRECTNESS findings, three
of which Claude independently verified against the repository as **genuine errors in this
document**. See `docs/research/exp062_codex_challenge_v1.md`. Not CONSENSUS. Nothing is authorized.
A consolidated v2 correction is required before any build.

**Known-wrong in this version, do not act on it:**
- §0's claim that all four prior probes moved division is **false** — exp_055 was an edge
  intervention whose entire proxy gain was adjusted-edge with division unchanged, and its LB delta
  was still 0.000. The "first edge lever" framing must go.
- §2's axis description is **reversed** — the tensor is `[n_src, n_tgt]`, so rows are sources.
- §6 gate 5's monotonicity claim is **false** — column-best-only pairs gain `0.8β` and row-best-only
  pairs gain `0.3β`; only "neither" pairs lose (`−0.2β`).
- §7's claim that exp_060's lb-submit kernel disabled the PP sweep is **false** — the sweep ran and
  re-selected tight55, and the 1.3 h figure includes it.
- §8's automatic β = 0.40 escalation on a null is unjustified.

Author: Claude Code, 2026-09-23. Parent: `repro_059_public_0947_exact_copy` (Public LB **0.947**,
submission 56313491).

---

## 0. Why this, and why now

Four consecutive causally-isolated interventions returned **zero** Public LB movement:

| experiment | intervention | LB | delta |
|---|---|---|---|
| exp_055 | edge joint repair | 0.942 | 0.000 |
| exp_057 | motion EMA | 0.944 | 0.000 |
| exp_060 | safe-div threshold 0.20→0.18 | 0.947 | 0.000 |
| exp_061 | Z-reflection DeepCenter TTA (zon) | — | **never scored** (5 failed transports) |

**The common factor is not "post-processing is exhausted". It is that all four moved the
division term, which carries weight 0.1 in the aggregate.** exp_060's own telemetry made this
explicit: +40 accepted candidates and +11 net final forks changed the score by <0.0005 — a null
was arithmetically near-certain regardless of whether those forks were true or false.

This proposal is the first intervention in the arc that targets **edge association**, which carries
the remaining ~0.9 of the metric. It is also the first lever for which a **published, independent
pedigree** exists on our exact base (§2).

Context that bounds the decision: our 0.947 is now **outside the top 200** (rank-200 cutoff 0.949,
LB top 0.975) and the competition closes **2026-09-29 23:59** — roughly six days. Full recon:
`docs/research/public_frontier_recon_2026-09-23.md`.

## 1. Parent and deployment substrate

- **Parent (prediction policy):** `repro_059_public_0947_exact_copy`, submission SHA256
  `d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60`, Public LB 0.947.
- **Deployment substrate:** exp_060's **single-config variant-notebook** pattern — one notebook
  whose own `submission.csv` output *is* the candidate arm, submitted with
  `competition_submit_code`.

The substrate choice is not cosmetic and is a direct consequence of the exp_061 post-mortem. That
pattern is **the only transport in this project with a proven hidden-rerun record** (submission
56361673, COMPLETE at 0.947). The exp_061 arc burned five submissions and 3.094 GPU-h on bespoke
deployment adapters — two static-copy kernels (incorrect format) and three full-inference
adapters with custom watchdogs, caches and atomic-publication layers (unhandled rerun error, cause
never identified). **exp_062 introduces no new deployment machinery whatsoever.**

## 2. The intervention

A rank-prior added to the edge logits before the activation, exactly as published in
`haideptry/biohub-sota-0-948-mutual-best-density-2xt4` (which self-reports
`source_notebook_sha256: 3e65ca69…` — the documented upstream of our own parent — with
`metric_hack_used: false`, `public_output_used: false`, `organizer_labels_used: false`):

```python
# inserted immediately before the edge activation
_lb_mode = os.environ.get("BIOHUB_LB_SCORING_MODE", "none")
_lb_beta = float(os.environ.get("BIOHUB_LB_SCORING_BETA", "0"))
if _lb_mode in {"relative_rank", "mutual_best"}:
    _lb_col_prob = torch.softmax(raw.float(), dim=0)
    _lb_row_prob = torch.softmax(raw.float(), dim=1)
    _lb_col_best = torch.argsort(torch.argsort(-_lb_col_prob, dim=0), dim=0) == 0
    _lb_row_best = torch.argsort(torch.argsort(-_lb_row_prob, dim=1), dim=1) == 0
    _lb_mutual   = _lb_col_best & _lb_row_best
    _lb_rank_bonus = (_lb_beta * _lb_col_best.float()
                      + 0.50 * _lb_beta * _lb_row_best.float()
                      + 0.50 * _lb_beta * _lb_mutual.float())
    if _lb_mode == "mutual_best":
        _lb_rank_bonus = _lb_rank_bonus - 0.20 * _lb_beta * (~_lb_mutual).float()
    raw = raw + _lb_rank_bonus.to(raw.dtype)
```

**Mechanism in plain terms.** It is the classical *mutual nearest-neighbour* / ratio-test prior
applied to the learned edge score: a candidate pair that is simultaneously the best choice of its
source (column) and of its target (row) receives up to `2.0·β` of extra logit; a pair that is not
mutually best is penalised by `0.2·β`. Its purpose is to suppress **track hijacking**, where a
strong but non-reciprocal candidate steals a link from the cell that actually owns it. That failure
mode is a *fragmentation* source — and our own zero-GPU ceiling study
(`docs/research/exp057_A0_edge_upper_bound_results.md`) put fragmentation at the top of the
remaining edge headroom (+0.027 proxy ceiling), well above wrong-association (+0.0015).

**Independent pedigree.** `yudaiyamauchi` published a systematic five-arm series on this same axis
and same base — **A** hard-negative margin, **B** hard-negative strong, **C**
disagreement-adaptive, **D** relative rank, **E** mutual-best association. `haideptry` carries
`BIOHUB_LB_EXPLORATION_ID = "e-mutual-best"`, i.e. **E is the variant that survived that series**.
Those notebooks carry 0–2 votes, so the lever is not widely adopted and is unlikely to be priced
into the public frontier.

**What the pedigree is NOT.** `haideptry`'s "SOTA 0.948+" headline is **unverified**: that author
does not appear in the top 200 of the leaderboard (cutoff 0.949). This proposal therefore treats
β = 0.20 as *a published starting point*, not as a known gain.

## 3. Falsifiable hypothesis

> **H1.** Adding the mutual-best rank prior (β = 0.20) to the edge logits of the frozen 0.947
> pipeline, with every other parameter byte-identical to `repro_059`, changes the Public LB score
> by at least +0.001 relative to 0.947.

H1 is falsified by a Public LB score ≤ 0.947. The experiment is **not** scored on any local proxy
(§6 explains why).

Secondary, mechanistic, and checkable without the LB:

> **H2.** The prior is *active*: the arm's `submission.csv` differs from the parent's
> `d3453380…`, and the number of edges whose mutual-best status differs from the unpatched run is
> non-zero.

H2 failing while the patch is reported applied means the prior is a no-op at this β, which is a
**valid null**, not a defect — but it must be distinguished from the patch silently not applying
at all (§5, Risk 1).

## 4. Exact change and arms

Purely additive, byte-revertible, built with the existing parity-guard builder pattern
(`scripts/build_exp06x_*.py`): every injected line is `# exp062`-marked, a builder guard strips
those lines and asserts the remainder is byte-identical to the parent notebook.

Environment, and nothing else:

```
BIOHUB_LB_SCORING_MODE  = mutual_best      # "none" reproduces the parent exactly
BIOHUB_LB_SCORING_BETA  = 0.20             # arm parameter
```

**Two arms in one kernel run:**

| arm | β | purpose | expected output SHA |
|---|---|---|---|
| `beta000` | 0.00 | **real-pipeline byte-parity control** | **must equal** `d3453380…` |
| `beta020` | 0.20 | candidate | differs, or valid null |

The `beta000` control is the non-negotiable part of the design and follows exp_060's `thr020`
precedent, which is the single piece of evidence that made exp_060 credible. It proves on the real
GPU pipeline that the patch is inert at β = 0 — i.e. that the insertion did not perturb the parent
path through some route other than the intended bonus.

Only the `beta020` output is submitted. `beta000` is never submitted (it would be a duplicate of a
known 0.947).

## 5. Risks, in order of how much they worry me

**Risk 1 — the patch silently does not apply. (Highest.)**
The upstream implementation inserts the block by **string replacement against an anchor** in the
prediction script, and on a miss it merely prints `Note: Mutual-Best anchor found N times` and
**continues unpatched**. That would produce an arm byte-identical to the parent, which we would
record as "null" when in fact nothing was tested — wasting a submission and, worse, writing a false
negative into the project record. This is exactly the "false verified-null" defect Codex raised as
exp_061 admission v1 finding #2.
*Mitigation:* the anchor match count must be asserted `== 1` and the run must **fail closed**
(raise) on any other count, before any inference begins. The applied source is re-compiled and the
patched region is hash-recorded in telemetry.

**Risk 2 — a real regression, and a large one.**
Unlike every prior experiment in this arc, this perturbs the ~0.9-weighted term. A poorly chosen β
can plausibly cost more than 0.001. This is the price of leaving the sub-precision regime, and it
is the *intended* exposure — but it means the rollback must be instant and the stop rule strict
(§8).

**Risk 3 — β is borrowed, not derived.**
β = 0.20 comes from an author whose headline claim we could not verify. We have no local evidence
for its calibration on our pipeline.
*Mitigation:* the stop rule in §8 treats 0.20 as one probe, not as a starting point for a sweep;
only one follow-up β is permitted, and only under a specified condition.

**Risk 4 — dim-0/dim-1 semantics.**
`softmax(raw, dim=0)` vs `dim=1` must correspond to (candidates-per-target) and
(candidates-per-source) in **our** parent's tensor layout, not merely in the upstream author's.
If the axes are transposed relative to ours, the prior still runs and still produces a plausible
number, but it means something different.
*Mitigation:* a local executable test on the extracted parent function asserting the axis semantics
against a hand-constructed matrix with a known mutual-best pair. **This is the check I would most
like Codex to scrutinise**, because it fails silently and is not visible in any output artifact.

**Risk 5 — deadline.**
Six days. Each LB probe costs one full inference run. A multi-round admission loop of the kind
exp_060 (5 rounds) and exp_061 (4 rounds) went through would consume the remaining window without
producing a single scored probe. §9 addresses this directly and asks Codex to rule on it.

## 6. Validation, and what we explicitly do NOT do

**No local-proxy gate.** The frozen train16 proxy has now failed to transfer **twice** with large
margins (exp_055: proxy +0.01485 → LB 0.000; exp_057: 3714-edge diff → LB 0.000), and the public
`evgendvorkin` evolution table shows the same decoupling in a third party's data (its v30 proxy
*fell* to 0.9430 while its LB *rose* to 0.945). Gating this experiment on a proxy would add a full
validation pass of GPU cost for a signal we have repeatedly shown to be untrustworthy. **The Public
LB is the validation instrument**, per the standing 2026-09-18 user policy that submission count is
no longer a research constraint.

Local gates that **are** required before launch, all zero-GPU:

1. Builder parity guard: stripping `# exp062` lines reproduces the parent notebook byte-for-byte.
2. Executable test: β = 0 ⇒ the bonus tensor is **exactly** zero (not merely small).
3. Executable test: axis semantics, per Risk 4, on a constructed matrix with a known mutual-best pair.
4. Executable test: anchor-miss ⇒ raises (Risk 1 fail-closed), exercised with a deliberately
   corrupted anchor.
5. Executable test: monotonicity — a mutually-best pair's post-bonus logit is strictly greater than
   the same pair's pre-bonus logit for β > 0, and a non-mutual pair's is strictly lower.
6. Snapshot smoke against the immutable snapshot.

## 7. Budget and artifacts

- **GPU:** one kernel run, two sequential arms, **2.6 h reserved** (exp_060's single-arm run was
  ~1.3 h; the parent's adaptive PP-sweep is disabled via `BIOHUB_VALIDATOR_ENABLE=0` with tight55
  pinned explicitly, as in exp_060's lb-submit kernel). Remaining budget 20.399 h, six protected
  hours preserved → within policy and well inside `max_single_experiment_hours` 4.0.
- **Submissions:** exactly **one** (`beta020`), separately authorized by the user, against a cap of
  5/day with the remote history checked first.
- **Artifacts:** `submission_beta000.csv`, `submission_beta020.csv`, `exp062_telemetry.json`
  (anchor match count, patched-region hash, per-arm SHA, mutual-best edge counts and the
  changed-edge count vs control, effective config), gated `metrics.json`
  (`exp062_mutual_best_integrity_passed`).

## 8. Stop rule and rollback

Pre-registered, against the parent's 0.947:

| `beta020` Public LB | reading | action |
|---|---|---|
| **≥ 0.948** | H1 supported | adopt as new parent; **one** follow-up probe at β = 0.12 to check the direction of the gradient; then reassess |
| **== 0.947** | sub-precision or inert | if H2 showed the arm output *differs*, the prior is real but too weak → **one** probe at β = 0.40; if H2 showed no difference, the prior is inert at this scale → **stop the lever** and move to density-adaptive overrides |
| **≤ 0.946** | H1 falsified, prior is harmful | **revert immediately**, keep repro_059 0.947, **do not sweep β downward** — move to density-adaptive overrides |

**Rollback:** `BIOHUB_LB_SCORING_MODE=none` restores the parent byte-for-byte; the builder guard
guarantees the notebook strips back to the parent. No state outside the kernel is mutated.

**Hard stop on the arc:** at most **two** kernel runs and **two** submissions for this lever in
total. If the lever is not clearly positive after that, it is closed and lever 2
(density-adaptive overrides, `docs/research/public_frontier_recon_2026-09-23.md` §3) is next. This
ceiling exists because the deadline permits roughly three serious attempts and I would rather spend
them on three distinct mechanisms than on one β sweep.

## 9. The open governance question I want Codex to rule on

exp_060 required **5** admission rounds and exp_061 **4**, and the exp_061 post-mortem identified
the cause as structural: a zero-GPU local harness cannot prove real-GPU-pipeline behaviour, so a
diligent reviewer can always name another "verify X locally" item (`PROJECT_RISK_REVIEW.md` Risk
#8). With six days left and the project 200+ places off the frontier, **an admission loop of that
length would itself guarantee failure** — the experiment would expire unlaunched, as exp_058 did.

I am therefore proposing an explicit, bounded contract and asking Codex to accept, amend, or reject
it rather than to apply the usual open-ended standard:

- Codex challenges this strategy **once**, and classifies each finding as either
  **(a) correctness/leakage/fail-closed** — must be fixed before launch — or
  **(b) verification-depth** — recorded as an open item, not a blocker.
- Class (a) findings are fixed and re-reviewed. Class (b) findings do not gate launch.
- If Codex judges the whole approach unsound, it says so plainly and we do not launch at all.

I am not asking for a lower standard on correctness. I am asking for the *scope* of the gate to be
fixed in advance so the loop terminates. **If Codex disagrees that this is legitimate, that
disagreement should be returned to the user, not overridden by me.**

## 10. Questions for Codex

1. **Is the axis semantics check (Risk 4) sufficient**, or does the dim-0/dim-1 correspondence need
   to be established against our parent's actual tensor layout before launch in a way a constructed
   unit test cannot achieve?
2. **Is the `beta000` byte-parity control worth 1.3 GPU-h**, or do local gates 1–5 make it
   redundant — given that its exp_060 analogue was the evidence that made that experiment credible?
3. **Is β = 0.20 the right first probe**, or is a smaller first move (β = 0.12, the value appearing
   in the relative-rank variant) better given that this is the first time the arc touches the
   0.9-weighted term and a regression is now genuinely possible?
4. **Is dropping the local-proxy gate entirely defensible** on the transfer-failure evidence in §6,
   or does removing it leave the experiment with no pre-LB quality signal at all?
5. **Is the mechanism itself sound**, or is there a reason a mutual-best prior would be redundant
   on top of the parent's existing bidirectional harmonic fusion — which already blends forward and
   reverse edge probabilities and might therefore already encode most of the reciprocity signal?
   *(This is the strongest theoretical objection I can raise against my own proposal, and I have
   not been able to rule it out from the source alone.)*
6. **Is the §9 bounded-gate contract acceptable?**

---

## Appendix — what this proposal deliberately does not do

- It does not touch division. The ARMED option B (larger 0.15/0.12 safe-div move) remains
  outstanding but is division-side and ranks below this lever on the §0 evidence.
- It does not add the DivNet mitosis gate (recon lever 3): model-level, but division-weighted.
- It does not bundle density-adaptive overrides (recon lever 2). Bundling two changes would repeat
  the causal-isolation failure that `repro_059`'s own +0.003 suffers from
  (`experiments/repro_059_public_0947_exact_copy/PROVENANCE.md` §5) and would make a null
  uninterpretable.
- It does not rebuild any deployment adapter. exp_061's five failed transports settled that.

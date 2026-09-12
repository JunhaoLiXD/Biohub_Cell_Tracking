# Local joint graph pilot: completed analysis

## Decision

The fixed five-frame context hypothesis failed its preregistered incremental
benefit gate. Preserve terminal `REJECT_LOCAL_POLICY` for the context policy;
do not relabel the experiment PASS or launch it remotely. The predeclared
original-score control is a promising separate candidate, improving the frozen
train16 proxy by 0.01485368362467987. It requires its own hypothesis and fresh
review before any remote validation. No threshold, weight, or candidate-pool
parameter was changed in response to observed scores.

Behavior parent: `repro_041_public_0941_motion_ema`.
Evidence donor: `diag_051_public_0942_tracklet_evidence`.
Completed local record: `experiments/local_052_joint_graph_pilot_v1_attempt02`.
Protocol: `.private/research/diag052_protocol_v1.json`.
GPU consumption: zero. Tracked GPU balance stays 15.667408447732495 hours,
including the protected six hours. No remote launch, submission, promotion,
training, or external-model review occurred.

## Complete graph results

| Arm | Train16 proxy | Delta | Edge TP/FP/FN | Division TP/FP/FN |
| --- | ---: | ---: | --- | --- |
| No change | 0.9387332376874039 | 0 | 9135/468/439 | 4/8/8 |
| Original probability + joint repair | 0.9535869213120838 | +0.01485368362467987 | 9195/373/379 | 4/8/8 |
| Original probability + context + joint repair | 0.9519261693422604 | +0.013192931654856466 | 9186/381/388 | 4/8/8 |

Context minus original-score control is -0.001660751969823404. The required
+0.001 incremental benefit did not pass. All seven other context gates passed:
aggregate gain >=0.005, positive discovery and confirmation panels, positive
both-specimen changes, worst-video adjusted-edge delta >=-0.002, and global and
per-specimen division protection. This supports joint repair, not the claim that
the tested context contribution improves its score.

| Panel | Original-score delta | Context delta |
| --- | ---: | ---: |
| Discovery (8 videos) | +0.021017988319890324 | +0.01960957771265448 |
| Confirmation (8 videos) | +0.007023560368196957 | +0.005047942891353796 |
| 44b6 | +0.0033374477119612056 | +0.002241768526679566 |
| 6bba | +0.018923931597245702 | +0.017065883998374276 |

Original-score video signs: 9 improved, 6 unchanged, 1 regressed. Worst video
is `44b6_7a302da0` at -0.0018034644080261453, close to the -0.002 limit.
Context signs: 8 improved, 8 unchanged, none regressed. This is a real robustness
tradeoff, but was not a prespecified alternative advancement criterion.
The largest original-score video improvement is `6bba_0c7fa718` at
+0.1174928080487232; gains are heterogeneous and strongly concentrated.

## What changed

No nodes, coordinates, detection parameters, weights or EMA values changed.
Candidate extraction inspected all 5,013,443 cached pairs, retaining 3,030,025
pairs with persistent original endpoints. Top-eight selection plus existing
links retained 2,652,691 pairs. Both scored arms used the same pool.
Complete five-frame geometric context existed for 2,315,839 retained pairs.
This is geometry from t-2 through t+2 plus existing two-frame secondary
appearance, not a newly trained five-frame encoder.

Maximum-weight bipartite assignment jointly resolved competing source/target
slots per frame, retaining no-change choices and charging additions/removals.
Existing forks and adjacent edges, uncached existing edges and uniquely top-ranked
existing probability >=0.9 links were protected. No new forks were created.
Pure-deletion components and components with nonpositive utility gain were
reverted. Current nodes and contexts were frozen throughout, so temporal
consistency after simultaneous edits remains a limitation.

Original-score policy: 1,419 actions, 2,582 added and 2,781 removed edges.
Relative to 366,116 parent edges, symmetric edit rate is 1.4648%.
Context policy: 1,144 actions, 2,086 added and 2,194 removed edges; rate 1.1690%.

| Edit evidence | Original-score | Context |
| --- | ---: | ---: |
| Added true | 64 | 54 |
| Removed true | 4 | 3 |
| Added annotation-supported false | 20 | 10 |
| Removed annotation-supported false | 115 | 97 |
| Added unknown | 2498 | 2022 |
| Removed unknown | 2662 | 2094 |

The frozen scorer's sparse-annotation FP rules were applied independently, not
an assumption that every non-GT edge is false. Most edits remain unknown. It is
not justified to call all unscored edits safe or to estimate deployment precision
from the annotated subset.

## Corrections and verification

The old residual diagnostic's tie test incorrectly expected rank 3 for two tied
best candidates; corrected expected worst-tie rank is 2. New regression coverage
selects noncontiguous original rows and a nonzero singleton row with distinct
probabilities, logits and acceptance values. The fixed diagnostic reproduced all
16 videos and its 109/212/241 top-1/top-3/top-8 probability counts, 242 residuals,
85 accepted residuals and 2,223 candidate rows.

The first full-graph attempt stopped on its second video when a cached original
frame-99 node ID 46717 was reused by a recovered final-frame-4 node. The failure
and original source snapshot remain in `experiments/local_052_joint_graph_pilot_v1`.
An integrity-only amendment requires unchanged frame identity and node presence
through all nine exported graph stages. Fifteen final numeric IDs fail this test.
No aggregate result had been evaluated before the amendment. Parameters and
panels were unchanged. A separate identity-checked residual diagnostic v3 confirms
that all previous residual ranking counts remain identical.

Thirteen focused tests passed, including occupied-endpoint joint swaps, order
invariance, no-change, protected and uncached links, fork preservation,
five-frame availability, context choice, pure-deletion rejection and ID reuse.
The full run verified all 1,776 evidence files against their manifests.
Independent audit reconstructed all 48 graphs from action logs, confirmed exact
node preservation, graph degrees/time, fork identities, all frozen score fields,
edit labels, graph hashes and aggregate arithmetic. See the run's `audit.json`.

Discovery/confirmation groups were frozen by sorted video IDs within each
specimen before scoring; no fitting or parameter selection was performed. The
data were used in prior project analyses and pretrained feature extractors saw
train16. These are grouped fixed-policy panels, not a clean unseen holdout or
independent generalization estimate. Both specimen panels are descriptive
transfer stress checks, not two trained leave-specimen-out models.

## Next concrete candidate

Recommend a new original-score joint-repair validation hypothesis, preserving
this exact rule without context or further tuning. Design:
`.private/research/diag052_original_score_successor_design.md`.
The context gate stays rejected. Do not interpret the local 0.9535869 proxy as a
Public LB prediction or compare it numerically to the verified 0.944 Public LB.

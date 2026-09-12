# Proposed original-score joint-repair validation

Status: concrete follow-up design, not a launched experiment or an admission PASS.
This is a new hypothesis motivated by a predeclared control; the failed context
increment gate is retained, not waived.

## Hypothesis and parent

Using the original cached pair probability in a protected joint cut-and-reconnect
step improves complete graph association over reproduced EMA 0.4. Behavior parent
is `repro_041_public_0941_motion_ema`; diag_051 is the evidence donor, and
`local_052_joint_graph_pilot_v1_attempt02` is the local discovery record.
Validation protocol remains `public_0941_frozen_train16_stratified_proxy_v1`.

## Exact change

Port only the `original_score` arm from the immutable local run snapshot. Keep
top k=8, probability protection=0.9, edit penalty=0.25, per-frame joint assignment,
no-change and pure-deletion rejection unchanged. Preserve existing forks and
adjacent edges, nodes, coordinates, models and EMA 0.4. No added motion/cosine term,
new node creation, new fork creation, training or threshold sweep.

Production integration must use prediction-only graph data at the same final
postprocessing stage for both test and validation. It must not rely on the
`final_scored` file or scorer matching to identify valid nodes. Keep an explicit
immutable detection provenance ID through recovery so deleted numeric IDs cannot
be reused as evidence for new nodes. Verify cache availability for protected
existing edges and ensure the original-score-only candidate extraction does not
depend on appearance or motion values. Tie ordering and SciPy version must be
pinned. The current prototype unnecessarily computes context features for the
control; remove that work only after exact-output equivalence is demonstrated.

## Admission and parity checks

1. Match all 16 cached original-score output graphs and score rows from the local
   run, not merely aggregate score. Expected proxy: 0.9535869213120838;
   edge TP/FP/FN 9195/373/379, division 4/8/8.
2. Demonstrate unchanged no-change baseline and GT-blind test execution. Test
   node-ID reuse, occupied-endpoint swaps, forks, missing candidates, timestamps,
   deterministic ties, dependency availability and CSV graph integrity.
3. Run one fresh experiment-specific Claude review after the final notebook,
   config and snapshot are concrete. Exact model allowance is unavailable;
   disclose this before the bounded review and do not retry timeout/quota stops.
4. Snapshot smoke PASS, explicit experiment record and <=2 GPU-hour reservation,
   preserving six hours. No remote launch is justified by the context experiment's
   terminal result alone; the separate original-score design must be reviewed.

## Advancement checks for the proposed run

Require exact cached validation graph reproduction, >=0.005 versus parent,
positive changes in both specimens and both fixed video panels, worst-video
adjusted-edge delta >=-0.002, and unchanged or improved global/per-specimen
division counts. Report newly broken true links and unknown edit burden.
No Public LB score is implied. A leaderboard submission remains separately
authorized, subject to remote history and duplicate/daily-budget checks.

## Risks and fallback

Most edits are outside annotation support. The original-score control loses
0.00180346 on one video and most aggregate benefit comes from 6bba; it may not
transfer to the hidden set. Local node provenance must match production exactly.
Retain reproduced EMA 0.4 and verified Public LB 0.944 as separate fallbacks.
Do not launch a second parameter arm to rescue a failed remote parity/gain result.

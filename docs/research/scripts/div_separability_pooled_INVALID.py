"""Zero-GPU separability check: does DeepCenter safe-division score separate
candidates that map a real GT division from those that don't?

*** METHODOLOGICALLY INVALID — PRESERVED FOR PROVENANCE ONLY (2026-09-16). ***
Codex challenge v1 (docs/research/exp057_post_null_codex_challenge_v1.md, finding 3)
showed the "pooling across 6 runs" here is PSEUDO-REPLICATION: the 6
validator_safe_division_causal_audit.jsonl files are only 3 distinct files
(byte-identical triples/pairs) and all contain the SAME two positive sites (both
6bba). Pooling does NOT raise the positive experimental unit above 2, so the
"pooled AUC escapes N=2" conclusion in the diagnostic's original section 6a is
withdrawn. The audit files also have deepcenter_safe_div_veto=false, unlike the
production 0.944 gate (veto @0.25), so they are not even the production population.
Do NOT cite this pooled AUC as evidence. A correct exact-0.944-lineage audit is the
A0 step in exp057_post_null_strategy_proposal.md v2. Frozen provenance (the exact 6
inputs consumed on 2026-09-16, their SHA256s, the 3 distinct-hash groups, and the
captured output) is in div_separability_pooled_INVALID_manifest.json — that manifest,
not this script's live glob, is the provenance record.

Pools all locally available validator_safe_division_causal_audit.jsonl files.
Reports per-run and pooled AUC using two labels:
  (1) source_maps_gt_division  (direct GT mapping; far less sparse)
  (2) causal_delta_tp>0 vs causal_delta_fp>0 (the sparse one diag_013 used)
"""
import json
from pathlib import Path

ROOT = Path(r"E:/Project/Biohub_CellTracking")
FILES = sorted(ROOT.glob("experiments/*/artifacts/validator_safe_division_causal_audit.jsonl"))


def auc(scores_pos, scores_neg):
    """Mann-Whitney AUC = P(score_pos > score_neg). None if either side empty."""
    if not scores_pos or not scores_neg:
        return None
    # rank-based
    allv = [(s, 1) for s in scores_pos] + [(s, 0) for s in scores_neg]
    allv.sort(key=lambda x: x[0])
    # assign average ranks
    ranks = [0.0] * len(allv)
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1][0] == allv[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # 1-indexed average rank
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    sum_pos = sum(r for r, (_, lab) in zip(ranks, allv) if lab == 1)
    n_pos = len(scores_pos)
    n_neg = len(scores_neg)
    u = sum_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def analyze(records, tag):
    pos_gt = [r["deepcenter_score"] for r in records if r.get("source_maps_gt_division")]
    neg_gt = [r["deepcenter_score"] for r in records if not r.get("source_maps_gt_division")]
    a_gt = auc(pos_gt, neg_gt)

    caus_tp = [r["deepcenter_score"] for r in records if r.get("causal_delta_tp", 0) > 0]
    caus_fp = [r["deepcenter_score"] for r in records if r.get("causal_delta_fp", 0) > 0]
    a_caus = auc(caus_tp, caus_fp)

    print(f"\n== {tag} ==")
    print(f"  candidates: {len(records)}")
    print(f"  source_maps_gt_division: pos={len(pos_gt)} neg={len(neg_gt)}")
    if a_gt is not None:
        print(f"  AUC(deepcenter_score -> maps_gt_division): {a_gt:.3f}  "
              f"(0.5=no signal; >0.5 high-score=>true, <0.5 low-score=>true)")
    print(f"  causal: TP-edges={len(caus_tp)} FP-edges={len(caus_fp)}")
    if a_caus is not None:
        print(f"  AUC(deepcenter_score -> causal TP vs FP): {a_caus:.3f}")
    return pos_gt, neg_gt, caus_tp, caus_fp


pooled = []
allpos_gt = allneg_gt = allcaus_tp = allcaus_fp = None
agg = {"pos_gt": [], "neg_gt": [], "caus_tp": [], "caus_fp": []}

for f in FILES:
    exp = f.parts[-3]
    recs = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    p, n, ct, cf = analyze(recs, exp)
    agg["pos_gt"] += p; agg["neg_gt"] += n; agg["caus_tp"] += ct; agg["caus_fp"] += cf
    pooled += recs

print("\n" + "=" * 60)
a_gt = auc(agg["pos_gt"], agg["neg_gt"])
a_caus = auc(agg["caus_tp"], agg["caus_fp"])
print("POOLED across all runs (same 16 videos, identical DeepCenter epoch-2 gate)")
print(f"  total candidates: {len(pooled)}")
print(f"  source_maps_gt_division: pos={len(agg['pos_gt'])} neg={len(agg['neg_gt'])}")
print(f"  AUC(deepcenter_score -> maps_gt_division): {a_gt:.3f}")
print(f"  causal TP-edges={len(agg['caus_tp'])} FP-edges={len(agg['caus_fp'])}")
if a_caus is not None:
    print(f"  AUC(deepcenter_score -> causal TP vs FP): {a_caus:.3f}")

# Simple separation summary: median score for pos vs neg (GT-mapping label)
def med(xs):
    xs = sorted(xs)
    return xs[len(xs)//2] if xs else float("nan")
print(f"\n  median deepcenter_score  maps_gt=True : {med(agg['pos_gt']):.3e}")
print(f"  median deepcenter_score  maps_gt=False: {med(agg['neg_gt']):.3e}")

"""A0 Part 1 — scorer-aware edge/detection/node upper-bound audit (zero-GPU).

Reads the exact-0.944-lineage val_049 per-video validator_results.csv, reconstructs
the frozen scorer EXACTLY (validated against metrics.json primary_metric
0.9310696298996892), then computes OPTIMISTIC ceilings: the maximum run-level
Delta-score achievable if each bounded error class were perfectly corrected.

These are UPPER BOUNDS on the train16 proxy, not achievable gains and not LB gains.
Their purpose is to RANK levers and decide whether any edge/detection sub-target has
enough headroom to justify further work (Codex challenge v1/v2, A0 step 1).

Scorer (from biohub_tracking/metrics.py, verified):
  per-sample: edge_jaccard = tp/(tp+fp+fn)
              total_node_ratio = (num_pred_nodes - n_total)/n_total   [t_pred,t_true]
              adj = max(0, edge_jaccard*(1 - 0.1*total_node_ratio))
  run: adj = sum(w_i*adj_i)/sum(w_i),  w_i = tp+fp+fn
       div_jaccard = sum(tp)/(sum tp+fp+fn)
       score = adj + 0.1*div_jaccard
"""
import csv
from pathlib import Path

ALPHA = 0.1
DIV_W = 0.1
CSV = Path(r"E:/Project/Biohub_CellTracking/experiments/val_049_public_0944_train16/artifacts/validator_results.csv")
BASELINE_SCORE = 0.9310696298996892


def load():
    rows = []
    with CSV.open() as f:
        for r in csv.DictReader(f):
            rows.append({
                "stem": r["stem"],
                "tp": int(r["edge_tp"]), "fp": int(r["edge_fp"]), "fn": int(r["edge_fn"]),
                "t_pred": float(r["t_pred"]), "t_true": float(r["t_true"]),
                "wae": int(r["wrong_association_edges"]),
                "frag": int(r["edges_fragmented"]),
                "lost": int(r["edges_lost_to_detection"]),
                "spurious": int(r["spurious_pred_nodes"]),
                "div_tp": int(r["div_tp"]), "div_fp": int(r["div_fp"]), "div_fn": int(r["div_fn"]),
            })
    return rows


def adj_sample(tp, fp, fn, t_pred, t_true):
    denom = tp + fp + fn
    if denom <= 0:
        return None, 0
    ej = tp / denom
    ratio = (t_pred - t_true) / t_true if t_true > 0 else float("nan")
    adj = max(0.0, ej * (1 - ALPHA * ratio))
    return adj, denom


def run_score(rows, edge_mut=None, node_perfect=False, div_counts=None):
    """edge_mut(row)->(tp,fp,fn,t_pred) override; node_perfect sets ratio=0."""
    num = den = 0.0
    for r in rows:
        tp, fp, fn, t_pred = r["tp"], r["fp"], r["fn"], r["t_pred"]
        if edge_mut:
            tp, fp, fn, t_pred = edge_mut(r)
        t_true = r["t_true"]
        if node_perfect:
            t_pred = t_true  # ratio -> 0
        adj, w = adj_sample(tp, fp, fn, t_pred, t_true)
        if adj is None:
            continue
        num += w * adj
        den += w
    adj_run = num / den if den else float("nan")
    if div_counts is None:
        dtp = sum(r["div_tp"] for r in rows)
        dfp = sum(r["div_fp"] for r in rows)
        dfn = sum(r["div_fn"] for r in rows)
    else:
        dtp, dfp, dfn = div_counts
    div_j = dtp / (dtp + dfp + dfn) if (dtp + dfp + dfn) > 0 else float("nan")
    return adj_run + DIV_W * div_j, adj_run, div_j


def clampfix(r, keys):
    """Optimistic fix: for each edge in the named classes, tp+=1, fp-=1(if wae), fn-=1."""
    tp, fp, fn, t_pred = r["tp"], r["fp"], r["fn"], r["t_pred"]
    n = sum(r[k] for k in keys)
    # wrong-association fix moves fp->tp and recovers the fn; frag/lost fix recovers fn->tp
    if "wae" in keys:
        w = r["wae"]
        take_fp = min(w, fp)
        tp += take_fp; fp -= take_fp
        take_fn = min(w, fn)
        fn -= take_fn
        n -= r["wae"]  # handled; remaining keys are fn-recovery only
    for k in keys:
        if k == "wae":
            continue
        rec = min(r[k], fn)
        tp += rec; fn -= rec
    return tp, fp, fn, t_pred


rows = load()
base, base_adj, base_div = run_score(rows)
print(f"BASELINE reconstruct: score={base:.16f}  adj_edge={base_adj:.10f}  div_j={base_div:.6f}")
print(f"  expected         : score={BASELINE_SCORE:.16f}   (match={abs(base-BASELINE_SCORE)<1e-9})")
tot = lambda k: sum(r[k] for r in rows)
print(f"  totals: edge tp/fp/fn = {tot('tp')}/{tot('fp')}/{tot('fn')} (union {tot('tp')+tot('fp')+tot('fn')})")
print(f"          wrong_assoc={tot('wae')} fragmented={tot('frag')} detection_lost={tot('lost')}")
print(f"          div tp/fp/fn = {tot('div_tp')}/{tot('div_fp')}/{tot('div_fn')}  spurious_nodes={tot('spurious')}")
print()

def ceiling(name, **kw):
    s, a, d = run_score(rows, **kw)
    print(f"  {name:52s} score={s:.6f}  delta={s-base:+.6f}  (adj={a:.6f} div_j={d:.4f})")
    return s - base

print("=== EDGE / NODE upper-bound ceilings (optimistic, train16 proxy) ===")
ceiling("fix wrong-association edges only", edge_mut=lambda r: clampfix(r, ["wae"]))
ceiling("fix fragmentation edges only", edge_mut=lambda r: clampfix(r, ["frag"]))
ceiling("fix detection-loss edges only", edge_mut=lambda r: clampfix(r, ["lost"]))
ceiling("perfect node count (ratio->0, remove adjustment)", node_perfect=True)
ceiling("fix ALL edge classes (wae+frag+lost)", edge_mut=lambda r: clampfix(r, ["wae","frag","lost"]))
ceiling("fix ALL edges + perfect nodes", edge_mut=lambda r: clampfix(r, ["wae","frag","lost"]), node_perfect=True)
print()
print("=== DIVISION ceilings ===")
ceiling("division: remove all FP (3/0/9)", div_counts=(3,0,9))
ceiling("division: FP->0 and recover half FN (8/0/4)", div_counts=(8,0,4))
ceiling("division: perfect (12/0/0)", div_counts=(12,0,0))
print()
print("NOTE: all delta are OPTIMISTIC ceilings on the 16-video train16 proxy, not")
print("achievable gains and NOT Public LB gains. Ranking/headroom only.")

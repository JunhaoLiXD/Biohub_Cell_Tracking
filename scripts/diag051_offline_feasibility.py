"""Zero-GPU residual-conditioned ranking diagnostic, not a policy evaluation.

This screen does not mutate graphs or train weights. It measures whether existing
candidate logits and appearance vectors can rank the known missing GT links in a
candidate pool. GT selects the residual sources as well as evaluation labels.
"""
from __future__ import annotations

import gzip
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "experiments/diag_051_public_0942_tracklet_evidence/artifacts"
OUT = ROOT / ".private/research/diag051_audit/offline_feasibility_v2.json"


def read_json_gz(path: Path):
    return json.loads(gzip.decompress(path.read_bytes()))


def cosine(a, b):
    denom = np.linalg.norm(a, axis=1) * np.linalg.norm(b)
    return (a @ b) / np.maximum(denom, 1e-12)


def rank_stats(items, score_key):
    """Per-video rank of residual positives among all candidates from each source.

    Candidate labels are deliberately not used to form the ranking pool.  A
    candidate with an unmapped endpoint is unlabeled, but it is still a real
    candidate that can outrank a residual edge.  Equal scores use the
    conservative worst rank (all tied candidates count ahead).
    """
    by_source = defaultdict(list)
    for item in items:
        by_source[item["source"]].append(item)
    ranks = []
    for item in items:
        if not item["positive"]:
            continue
        peers = by_source[item["source"]]
        higher = sum(float(p[score_key]) > float(item[score_key]) for p in peers)
        ties = sum(float(p[score_key]) == float(item[score_key]) for p in peers)
        # ``ties`` includes the item itself; counting the other tied rows gives
        # the conservative rank while allowing a unique maximum to be rank 1.
        ranks.append(1 + higher + max(0, ties - 1))
    if not ranks:
        return dict(n=0, top1=0, top3=0, top8=0, median_rank=None)
    return dict(n=len(ranks), top1=sum(r <= 1 for r in ranks),
                top3=sum(r <= 3 for r in ranks), top8=sum(r <= 8 for r in ranks),
                median_rank=float(np.median(ranks)))


def extract_candidate_records(
    pair,
    graph_ids,
    positive_sources,
    mapped_gt,
    missing,
    pred_node_ids,
    mapped_pred_ids,
):
    """Extract aligned candidate rows from one pair artifact.

    ``pair_indices`` is filtered by source first.  ``original_indices`` keeps
    every subsequent value (probability, logits, status) aligned to its
    original pair row; indexing those arrays by the filtered row number was the
    v1 bug.  ``label`` is ``positive``, ``negative``, or ``unlabeled``.
    """
    ij = np.asarray(pair["pair_indices"])
    src_ids = graph_ids[np.asarray(pair["source_ids"])]
    tgt_ids = graph_ids[np.asarray(pair["target_ids"])]
    source_values = np.fromiter(positive_sources, dtype=src_ids.dtype)
    keep = np.isin(src_ids[ij[:, 0]], source_values)
    original_indices = np.flatnonzero(keep)
    filtered_ij = ij[original_indices]
    pred_node_ids = set(pred_node_ids)
    mapped_pred_ids = set(mapped_pred_ids)

    pfeat_s, pfeat_t = pair["primary_source_features"], pair["primary_target_features"]
    sfeat_s, sfeat_t = pair["secondary_source_features"], pair["secondary_target_features"]
    by_i = defaultdict(list)
    for k, (i, j) in enumerate(filtered_ij):
        by_i[int(i)].append((k, int(j)))
    p_cos_by_k, s_cos_by_k = {}, {}
    for i, pairs in by_i.items():
        js = np.asarray([j for _, j in pairs], dtype=np.int64)
        pc = cosine(pfeat_t[js], pfeat_s[i])
        sc = cosine(sfeat_t[js], sfeat_s[i])
        for (k, _), pv, sv in zip(pairs, pc, sc):
            p_cos_by_k[k], s_cos_by_k[k] = float(pv), float(sv)

    records = []
    for k, (i, j) in enumerate(filtered_ij):
        src, tgt = int(src_ids[i]), int(tgt_ids[j])
        if src not in pred_node_ids or tgt not in pred_node_ids:
            continue
        pair_key = (src, tgt)
        if pair_key in missing:
            label = "positive"
        elif src in mapped_pred_ids and tgt in mapped_pred_ids:
            label = "negative" if pair_key not in mapped_gt else "known_positive"
        else:
            label = "unlabeled"
        row = int(original_indices[k])
        records.append(dict(
            source=src, target=tgt, label=label,
            positive=label == "positive", missing_positive=label == "positive",
            probability=float(pair["probabilities"][row]),
            primary_cosine=float(p_cos_by_k[k]), secondary_cosine=float(s_cos_by_k[k]),
            blended=float(pair["blended_logits"][row]), status=int(pair["status"][row]),
        ))
    return records


def main():
    metrics = json.loads((ART / "metrics.json").read_text())
    graph_manifest = metrics["metrics"]["evidence_graph_manifest"]
    videos = []
    rankings = defaultdict(list)
    for stem in sorted(graph_manifest):
        folder = ART / "tracklet_evidence" / stem
        final = read_json_gz(folder / "final_scored.json.gz")
        pn, gn = dict(final["pred_nodes"]), dict(final["gt_nodes"])
        matching = read_json_gz(folder / "scorer_matching.json.gz")
        p2g, g2p = dict(matching["p2g"]), dict(matching["g2p"])
        pred_edges = {tuple(e) for e in final["pred_edges"]}
        gt_edges = {tuple(e) for e in final["gt_edges"]}
        mapped_gt = {(g2p[s], g2p[t]) for s, t in gt_edges if s in g2p and t in g2p}
        missing = mapped_gt - pred_edges
        positive_sources = {s for s, _ in missing}
        reg = np.load(folder / "pre_ilp_nodes.npz", allow_pickle=False)
        graph_ids = reg["graph_node_ids"]
        records = []
        for t in range(99):
            with np.load(folder / f"pair_{t:03d}_{t+1:03d}.npz", allow_pickle=False) as z:
                records.extend(extract_candidate_records(
                    z, graph_ids, positive_sources, mapped_gt, missing, pn, p2g
                ))
        # Rank residual links against all observed final-node competitors.
        # Existing true links remain known positives, not negative training labels.
        residual = [dict(x, positive=x["missing_positive"]) for x in records]
        for score_name in ["probability", "blended", "primary_cosine", "secondary_cosine"]:
            stats = rank_stats(residual, score_name)
            # Preserve the score field name for output and compute manually per score.
            stats["score"] = score_name
            rankings[score_name].append((stem, stats))
        print(f"{stem}: candidates={len(records)} residual={sum(x['missing_positive'] for x in records)} accepted={sum(x['missing_positive'] and x['status'] == 2 for x in records)}")
        videos.append(dict(stem=stem, candidate_rows=len(records), residual_positives=sum(x["missing_positive"] for x in records),
                           accepted_residual=sum(x["missing_positive"] and x["status"] == 2 for x in records),
                           rows=records))
    summary = dict()
    for score_name, vals in rankings.items():
        total = sum(v["n"] for _, v in vals)
        summary[score_name] = dict(videos=len(vals), residuals=total,
            top1=sum(v["top1"] for _, v in vals), top3=sum(v["top3"] for _, v in vals),
            top8=sum(v["top8"] for _, v in vals), median_ranks=[v["median_rank"] for _, v in vals if v["median_rank"] is not None])
    specimen_stats = {}
    for specimen in sorted({v["stem"].split("_", 1)[0] for v in videos}):
        subset = [v for v in videos if v["stem"].startswith(specimen + "_")]
        specimen_stats[specimen] = dict(videos=len(subset), candidate_rows=sum(v["candidate_rows"] for v in subset),
            residual_positives=sum(v["residual_positives"] for v in subset),
            accepted_residual=sum(v["accepted_residual"] for v in subset))
    result = dict(protocol="residual_source_conditioned_rank_diagnostic_v2", videos=len(videos),
                  candidate_rows=sum(v["candidate_rows"] for v in videos),
                  residual_positives=sum(v["residual_positives"] for v in videos),
                  accepted_residual=sum(v["accepted_residual"] for v in videos),
                  per_video=[{k: v[k] for k in ("stem", "candidate_rows", "residual_positives", "accepted_residual")} for v in videos],
                  per_specimen=specimen_stats,
                  ranking_summary=summary,
                  limitations=["No weights were trained; this is a fixed-feature ranking screen.",
                               "GT selects residual sources and links; this is not a deployable policy or grouped holdout.",
                               "Top-k recall does not model joint degree conflicts or score impact.",
                               "Final-node mapping excludes node-creation and unmatched-endpoint cases."])
    OUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

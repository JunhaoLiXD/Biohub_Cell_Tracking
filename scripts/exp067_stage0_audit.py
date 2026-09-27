"""Stage 0 Q1: candidate-headroom audit. Zero GPU, CPU only, read-only over cached exports.

The question, which only became answerable once exp_067d exported bounded alternatives:

    Do the exported candidate sets even CONTAIN the edits a perfect model would need
    to recover a missed division?

This is an ORACLE UPPER BOUND computed with ground-truth labels. It is a DIAGNOSIS, not a
deployable result, and must never be quoted as performance. If the answer is no, no amount of
supervision rescues the exp067 architecture and the arc is over for zero GPU.

Distinct from the 2026-09-25 Step 0 audit, which asked whether POST-PROCESSING could recover the
missed divisions and measured false. This asks whether the candidate sets contain the edges at all.

Three levels are reported per ground-truth division, because they fail differently:

  matched     mother and both daughters matched to predicted nodes at all
  in_parent   the parent graph already has both edges (a true positive; no headroom needed)
  raw         both edges exist among the exported candidate edges (raw reachability)
  actionable  a DIVISION EVENT over exactly those two daughters survives hypothesis generation
              and its geometry gates -- this is what the decoder can actually choose
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.exp067 import hypotheses as H  # noqa: E402
from scripts.exp067 import provenance as P  # noqa: E402
from scripts.exp067 import supervise as S  # noqa: E402
from scripts.exp067.config import Exp067Config  # noqa: E402

EXPORT = ROOT / '.private/runtime/exp067d_out/exp067_export'
CONFIG = ROOT / 'configs/exp_067_temporal_joint_lineage.json'


def gt_divisions(labels):
    """Ground-truth mothers with >=2 children, mapped into predicted node ids where possible."""
    gt_to_pred = {}
    for pred, gt in labels.pred_to_gt.items():
        gt_to_pred.setdefault(int(gt), int(pred))
    events = []
    for mother, degree in labels.gt_out_degree.items():
        if int(degree) < 2:
            continue
        children = sorted(labels.gt_children.get(int(mother), []))[:2]
        events.append({
            'gt_mother': int(mother),
            'gt_children': [int(c) for c in children],
            'pred_mother': gt_to_pred.get(int(mother)),
            'pred_children': [gt_to_pred.get(int(c)) for c in children],
        })
    return events


def audit_stem(stem: str, config: Exp067Config) -> dict:
    graph = P.load_final_graph(EXPORT / f'{stem}.final.npz')
    evidence = P.load_evidence(EXPORT / f'{stem}.npz')
    labels = S.load_label_set(EXPORT / 'labels' / f'{stem}.npz')
    table = P.reconcile(graph, evidence)
    hyp = H.generate(table, config)
    hyp.rebuild_index()

    parent_edges = graph.parent_edge_set()
    # hypotheses.py keys its arrays by node ROW index, not node id (see generate():134 building
    # parent_pairs through row_of_node, and _generate_events():339 indexing node_id[r]). The first
    # run of this audit compared node ids against that row-keyed set, so every lookup missed and it
    # reported a spurious "0 of 7 reachable". Everything hypothesis-side is in row space below.
    row_of_node = graph.row_of_node
    candidate_edges = set(hyp.index_of_edge)
    # Division events, keyed by (mother, frozenset(daughters)), split by geometry gate.
    events_all, events_geom = set(), set()
    for src, a, b, ok in zip(hyp.v_src, hyp.v_a, hyp.v_b, hyp.v_geometry_pass):
        key = (int(src), frozenset((int(a), int(b))))
        events_all.add(key)
        if bool(ok):
            events_geom.add(key)

    rows, tally = [], Counter()
    for event in gt_divisions(labels):
        mother, children = event['pred_mother'], event['pred_children']
        row = dict(event, stem=stem)
        row['matched'] = mother is not None and all(c is not None for c in children)
        tally['gt_divisions'] += 1
        if not row['matched']:
            tally['unmatched'] += 1
            rows.append(row)
            continue
        tally['matched'] += 1
        row['in_parent'] = all((mother, c) in parent_edges for c in children)
        if mother not in row_of_node or any(c not in row_of_node for c in children):
            row['raw'] = row['event_generated'] = row['actionable'] = False
            row['row_missing'] = True
            tally['missed' if not row['in_parent'] else 'in_parent'] += 1
            rows.append(row)
            continue
        r_mother = int(row_of_node[mother])
        r_children = [int(row_of_node[c]) for c in children]
        pair = [(r_mother, c) for c in r_children]
        row['raw'] = all(e in candidate_edges for e in pair)
        row['raw_missing'] = [e for e in pair if e not in candidate_edges]
        key = (r_mother, frozenset(r_children))
        row['event_generated'] = key in events_all
        row['actionable'] = key in events_geom
        if row['in_parent']:
            tally['in_parent'] += 1
        else:
            tally['missed'] += 1
            tally['missed_raw_reachable'] += int(row['raw'])
            tally['missed_event_generated'] += int(row['event_generated'])
            tally['missed_actionable'] += int(row['actionable'])
        rows.append(row)

    return {
        'stem': stem, 'n_nodes': graph.n_nodes, 'n_parent_edges': graph.n_edges,
        'n_candidate_edges': hyp.n_edges, 'n_division_events': hyp.n_events,
        'n_division_events_geometry_pass': int(np.count_nonzero(hyp.v_geometry_pass)),
        'n_parent_forks': int(np.count_nonzero(hyp.v_is_parent_fork)),
        'tally': dict(tally), 'rows': rows,
    }


def main() -> int:
    config = Exp067Config.load(CONFIG)
    stems = sorted(p.name[: -len('.final.npz')] for p in EXPORT.glob('*.final.npz'))
    if not stems:
        raise SystemExit(f'no exports found under {EXPORT}')
    results, total = [], Counter()
    for stem in stems:
        result = audit_stem(stem, config)
        results.append(result)
        total.update(result['tally'])
        t = result['tally']
        print(f"{stem:16} nodes={result['n_nodes']:6d} cand_edges={result['n_candidate_edges']:7d} "
              f"events={result['n_division_events']:6d} (geom_pass={result['n_division_events_geometry_pass']:5d}) "
              f"| GT div={t.get('gt_divisions',0)} matched={t.get('matched',0)} "
              f"in_parent={t.get('in_parent',0)} missed={t.get('missed',0)} "
              f"raw={t.get('missed_raw_reachable',0)} actionable={t.get('missed_actionable',0)}")

    print('\n' + '=' * 78)
    print('Q1 CANDIDATE-HEADROOM AUDIT  (oracle upper bound; a DIAGNOSIS, not performance)')
    print('=' * 78)
    g, m = total.get('gt_divisions', 0), total.get('missed', 0)
    print(f"  ground-truth divisions                : {g}")
    print(f"  mother and both daughters matched     : {total.get('matched', 0)}")
    print(f"  already correct in the parent graph   : {total.get('in_parent', 0)}")
    print(f"  MISSED by the parent (the headroom)   : {m}")
    print(f"    both edges present in candidates    : {total.get('missed_raw_reachable', 0)}")
    print(f"    a division event was generated      : {total.get('missed_event_generated', 0)}")
    print(f"    ...and it PASSES the geometry gates : {total.get('missed_actionable', 0)}  <-- decodable")
    actionable = total.get('missed_actionable', 0)
    print('\n  VERDICT:', 'HEADROOM EXISTS' if actionable else 'NO HEADROOM')
    if not actionable:
        print('  No missed division is reachable from the exported candidates. More supervision')
        print('  cannot help: the decoder is never offered the edit it would need to make.')
    out = ROOT / 'docs/research/exp067_stage0_q1_headroom.json'
    out.write_text(json.dumps({'total': dict(total), 'per_stem': results}, indent=2), encoding='utf-8')
    print(f'\n  written: {out.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

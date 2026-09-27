"""Stage 0 Q1 follow-up: WHY is every missed division unreachable?

0 of 7 is an absolute result, so before it is allowed to kill the arc it has to survive the
obvious alternative explanation: a bug in the audit. It also matters a great deal WHICH cause is
operating, because the causes have opposite consequences:

  * generator too narrow (top-k truncation)      -> the architecture is fine, the generator is not
  * daughters not on the next frame              -> adjacent-frame candidates can never express it
  * daughters too far in micrometres             -> max_edge_um excludes them by construction
  * mother or daughters not reconsiderable       -> they are outside set R, so never candidates
  * node ids do not line up                      -> the audit is wrong, not the arc
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.exp067 import hypotheses as H  # noqa: E402
from scripts.exp067 import provenance as P  # noqa: E402
from scripts.exp067 import supervise as S  # noqa: E402
from scripts.exp067.config import Exp067Config  # noqa: E402
from scripts.exp067_stage0_audit import EXPORT, CONFIG, gt_divisions  # noqa: E402


def main() -> int:
    config = Exp067Config.load(CONFIG)
    print(f"generation limits: max_edge_um={config.generation.max_edge_um} "
          f"max_alt_per_source={config.generation.max_alt_per_source} "
          f"max_alt_per_target={config.generation.max_alt_per_target} "
          f"n_geometric={config.generation.n_geometric}\n")
    findings = []
    for path in sorted(EXPORT.glob('*.final.npz')):
        stem = path.name[: -len('.final.npz')]
        graph = P.load_final_graph(path)
        evidence = P.load_evidence(EXPORT / f'{stem}.npz')
        labels = S.load_label_set(EXPORT / 'labels' / f'{stem}.npz')
        table = P.reconcile(graph, evidence)
        hyp = H.generate(table, config)
        hyp.rebuild_index()

        index = {int(v): i for i, v in enumerate(graph.node_id)}
        node_t = {int(v): int(t) for v, t in zip(graph.node_id, graph.node_t)}
        pos = table.positions_um
        parent_edges = graph.parent_edge_set()

        for event in gt_divisions(labels):
            mother, children = event['pred_mother'], event['pred_children']
            if mother is None or any(c is None for c in children):
                continue
            if all((mother, c) in parent_edges for c in children):
                continue  # already a true positive
            row = {'stem': stem, 'mother': mother, 'children': children}
            row['ids_present'] = mother in index and all(c in index for c in children)
            if not row['ids_present']:
                findings.append(row)
                continue
            mi = index[mother]
            row['t_mother'] = node_t[mother]
            row['t_children'] = [node_t[c] for c in children]
            row['dt'] = [node_t[c] - node_t[mother] for c in children]
            row['dist_um'] = [round(float(np.linalg.norm(pos[index[c]] - pos[mi])), 2)
                              for c in children]
            row['mother_reconsiderable'] = bool(table.reconsiderable[mi])
            row['children_reconsiderable'] = [bool(table.reconsiderable[index[c]]) for c in children]
            row['n_candidates_from_mother'] = len(hyp.edges_of_source.get(mother, []))
            row['candidate_targets'] = [int(hyp.e_tgt[k]) for k in hyp.edges_of_source.get(mother, [])]
            row['child_edge_present'] = [(mother, c) in hyp.index_of_edge for c in children]
            # How close did each daughter come to being offered at all?
            row['child_has_any_incoming_candidate'] = [
                len(hyp.edges_of_target.get(c, [])) for c in children]
            row['mother_out_degree_parent'] = int(graph.out_degree().get(mother, 0))
            findings.append(row)

    print(f"{'stem':16} {'mother':>8} {'dt':>10} {'dist_um':>16} {'recons':>8} {'#cand':>6} {'edges?':>12}")
    causes = {}
    for f in findings:
        if not f.get('ids_present', True):
            print(f"{f['stem']:16} {f['mother']:>8}  ID MISMATCH -- audit bug")
            causes['id_mismatch'] = causes.get('id_mismatch', 0) + 1
            continue
        rec = 'Y' if f['mother_reconsiderable'] else 'N'
        rec += ''.join('Y' if r else 'N' for r in f['children_reconsiderable'])
        print(f"{f['stem']:16} {f['mother']:>8} {str(f['dt']):>10} {str(f['dist_um']):>16} "
              f"{rec:>8} {f['n_candidates_from_mother']:>6} {str(f['child_edge_present']):>12}")
        if any(d != 1 for d in f['dt']):
            causes['daughter_not_next_frame'] = causes.get('daughter_not_next_frame', 0) + 1
        elif any(d > config.generation.max_edge_um for d in f['dist_um']):
            causes['beyond_max_edge_um'] = causes.get('beyond_max_edge_um', 0) + 1
        elif not f['mother_reconsiderable'] or not all(f['children_reconsiderable']):
            causes['outside_reconsiderable_set'] = causes.get('outside_reconsiderable_set', 0) + 1
        else:
            causes['generator_truncation'] = causes.get('generator_truncation', 0) + 1

    print('\n' + '=' * 78)
    print('WHY THE MISSED DIVISIONS ARE UNREACHABLE')
    print('=' * 78)
    for cause, n in sorted(causes.items(), key=lambda kv: -kv[1]):
        print(f'  {cause:32} {n}')
    out = ROOT / 'docs/research/exp067_stage0_q1_causes.json'
    out.write_text(json.dumps({'causes': causes, 'findings': findings}, indent=2), encoding='utf-8')
    print(f'\n  written: {out.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

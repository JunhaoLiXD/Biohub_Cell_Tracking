"""Bounded CPU closeout audit; never changes predictions or historical receipts."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.exp067 import provenance, supervise
from scripts.exp067.config import Exp067Config
from scripts.exp067.hypotheses import symmetric_event_geometry
from scripts.exp067.parent_scorer import compute_division_confusion


def main():
    export = ROOT / '.private/runtime/exp067d_out/exp067_export'
    source = ROOT / 'docs/research/exp067_stage0_q1_headroom.json'
    audit = json.loads(source.read_text(encoding='utf-8'))
    cfg = Exp067Config.load(ROOT / 'configs/exp_067_temporal_joint_lineage.json').generation
    controls = {'base': cfg, 'sym075': replace(cfg, safe_div_sister_symmetry_tau=.75),
                'tau_off_only': replace(cfg, safe_div_sister_symmetry_tau=0),
                'distance14_only': replace(cfg, safe_div_max_um=14),
                'distance14_tau_off': replace(cfg, safe_div_max_um=14, safe_div_sister_symmetry_tau=0)}
    rows, cases, hashes = [], [], {}
    for item in audit['per_stem']:
        stem = item['stem']
        gp, lp = export / f'{stem}.final.npz', export / 'labels' / f'{stem}.npz'
        graph, labels = provenance.load_final_graph(gp), supervise.load_label_set(lp)
        for path in (gp, lp):
            hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        edges = graph.parent_edge_set()
        nodes = {int(n): (int(t), *map(float, p)) for n, t, p in zip(graph.node_id, graph.node_t, graph.node_zyx)}
        reverse = {g: p for p, g in labels.pred_to_gt.items()}
        tp, fp, fn = compute_division_confusion(nodes, edges, labels.gt_nodes_plain, labels.gt_edges, labels.pred_to_gt, reverse)
        rows.append({'stem': stem, 'direct_parent_events': item['tally'].get('in_parent', 0), 'div_tp': tp, 'div_fp': fp, 'div_fn': fn})
        for row in item['rows']:
            if not row['matched'] or row['in_parent']:
                continue
            u = graph.row_of_node[row['pred_mother']]
            a, b = [graph.row_of_node[c] for c in row['pred_children']]
            geometry = {name: symmetric_event_geometry(graph.positions_um(), u, a, b, control) for name, control in controls.items()}
            cases.append({'stem': stem, 'gt_mother': row['gt_mother'], 'pred_mother': row['pred_mother'],
                          'raw_edges_present': row['raw'], 'd_a': geometry['base'][1], 'd_b': geometry['base'][2],
                          'sister': geometry['base'][3], 'asymmetry': geometry['base'][4],
                          'geometry_pass': {k: bool(v[0]) for k, v in geometry.items()}})
    original = list(csv.DictReader((export.parent / 'validator_results.csv').open(encoding='utf-8')))
    for row in rows:
        reference = next(r for r in original if r['stem'] == row['stem'] and r['config'] == 'base')
        assert all(row[k] == int(reference[k]) for k in ('div_tp', 'div_fp', 'div_fn')), row
    gpu = json.loads((ROOT / 'GPU_BUDGET.json').read_text())
    epoch_ids = ['exp_064_x138_verbatim_repro', 'exp_065_metric_aligned_pruning', 'exp_066_probe_cx03', 'exp_067c_temporal_feature_export_v3', 'exp_067d_temporal_feature_export_v4']
    charges = []
    for exp in epoch_ids:
        found = [float(r['actual_hours']) for r in gpu['consumed'] if r['experiment_id'] == exp]
        found += [float(r['hours']) for r in gpu.get('consumption_log', []) if r['experiment_id'] == exp]
        assert len(found) == 1, (exp, found)
        charges.append({'experiment_id': exp, 'hours': found[0]})
    expected = 20 - sum(r['hours'] for r in charges)
    # Historical manual charges mix six-decimal and full-precision hours.
    assert abs(expected - gpu['remaining_hours']) < 1e-6
    assert not gpu['reserved_hours'] and not gpu.get('active_reservations')
    result = {'scope': 'Local cached evidence only; no new prediction, training, decode, remote query or submission.',
              'division_rows': rows, 'division_totals': {k: sum(r[k] for r in rows) for k in ('direct_parent_events', 'div_tp', 'div_fp', 'div_fn')},
              'missed_direct_cases': cases, 'geometry_pass_counts': {k: sum(r['geometry_pass'][k] for r in cases) for k in controls},
              'caveat': 'Geometry feasibility is not candidate/event availability, decoder selection, or scorer gain. Existing raw-edge flags come from the preserved Q1 artifact; candidate generation was not rerun.',
              'budget': {'epoch_start_hours': 20, 'charges': charges, 'expected_remaining_hours': expected, 'ledger_remaining_hours': gpu['remaining_hours'], 'rounding_residual_hours': gpu['remaining_hours'] - expected, 'tolerance_hours': 1e-6, 'reservations': 0},
              'input_sha256': hashes}
    out = ROOT / 'docs/research/closeout_audit_2026-09-26.json'
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('division_totals', 'geometry_pass_counts', 'budget')}, indent=2))


if __name__ == '__main__':
    main()

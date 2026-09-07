"""Read-only audit and paired historical comparison of the completed 0.941 baseline."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from _bootstrap import PROJECT_ROOT
from experiment_controller.core import load_record, verify_snapshot
from experiment_controller.public_copy import aggregate, audit_submission

EXPERIMENT = 'val_039_public_0941_train16'


def close(a, b):
    if not math.isclose(float(a), float(b), rel_tol=0, abs_tol=1e-12):
        raise ValueError(f'Metric mismatch: {a} != {b}')


def analyze(root=PROJECT_ROOT):
    record = load_record(root, EXPERIMENT)
    verify_snapshot(root, record)
    if record['state'] != 'KEEP':
        raise ValueError('Baseline must pass collection before completed-run analysis')
    artifacts = root / 'experiments' / EXPERIMENT / 'artifacts'
    metrics = json.loads((artifacts / 'metrics.json').read_text(encoding='utf-8'))
    identity = json.loads((artifacts / 'inference_identity.json').read_text(encoding='utf-8'))
    stages = json.loads((artifacts / 'validation_stage_stats.json').read_text(encoding='utf-8'))
    submission = audit_submission(artifacts / 'submission.csv')
    expected = 'bf66c879298e71c5cce0326fbac5956ca567a344ae28f0d402dfc5003fba52bd'
    assert submission['sha256'] == identity['submission_sha256'] == expected
    assert all(identity['checks'].values()) and all(metrics['metrics']['checks'].values())
    assert metrics['metrics']['validation_contract_passed'] is True
    with (artifacts / 'validator_results.csv').open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        for key in ('weight', 'adjusted_edge_jaccard', 'div_tp', 'div_fp', 'div_fn'):
            row[key] = float(row[key])
    assert len(rows) == len({r['stem'] for r in rows}) == 16
    assert set(stages) == {r['stem'] for r in rows}
    aggregate_score = aggregate(rows)
    close(aggregate_score['primary_metric'], metrics['primary_metric'])
    scopes = {'aggregate': {
        'score': metrics['primary_metric'],
        'adjusted_edge_jaccard': metrics['validation']['adjusted_edge_jaccard'],
        'division_jaccard': metrics['validation']['division_jaccard'],
    }}
    for specimen, data in metrics['specimen_metrics'].items():
        selected = [r for r in rows if r['stem'].startswith(specimen + '_')]
        recomputed = aggregate(selected)
        for key in ('primary_metric', 'adjusted_edge_jaccard', 'division_jaccard'):
            close(recomputed[key], data[key])
        scopes[specimen] = {'score': data['primary_metric'],
                            'adjusted_edge_jaccard': data['adjusted_edge_jaccard'],
                            'division_jaccard': data['division_jaccard']}
    comparisons = {}
    for reference in ('val_008_public_0933_train16_launchable', 'repro_036_train16_motion_ema'):
        baseline = json.loads((root / 'experiments' / reference / 'metrics.json').read_text(encoding='utf-8'))
        for specimen in ('44b6', '6bba'):
            assert baseline['specimen_metrics'][specimen]['samples'] == metrics['specimen_metrics'][specimen]['samples']
        deltas = {}
        for scope, current in scopes.items():
            previous = ({'score': baseline['primary_metric'], **baseline['validation']}
                        if scope == 'aggregate' else
                        {'score': baseline['specimen_metrics'][scope]['primary_metric'], **baseline['specimen_metrics'][scope]})
            deltas[scope] = {k: current[k] - previous[k] for k in current}
        comparisons[reference] = deltas
    selected_stats = ('deepcenter_safe_div_checked', 'deepcenter_safe_div_accepted',
                      'deepcenter_safe_div_rejected', 'deepcenter_safe_div_missing',
                      'safe_divisions_added', 'safe_division_symmetry_rejected',
                      'motion_relink_skipped_large_frame')
    return {
        'experiment_id': EXPERIMENT, 'audit_passed': True,
        'submission_audit': submission, 'actual_checkpoint': identity['actual_checkpoint'],
        'scores': scopes, 'historical_deltas_not_gates': comparisons,
        'stage_counts_by_specimen': {s: {k: sum(v[k] for stem, v in stages.items() if stem.startswith(s + '_'))
                                        for k in selected_stats} for s in ('44b6', '6bba')},
        'error_summaries': {s: m['error_summary'] for s, m in metrics['specimen_metrics'].items()},
        'runtime_seconds': metrics['runtime_seconds'],
        'lowest_adjusted_edge_videos': sorted(
            [{'stem': r['stem'], 'adjusted_edge_jaccard': r['adjusted_edge_jaccard'],
              'division_tp': r['div_tp'], 'division_fp': r['div_fp'], 'division_fn': r['div_fn']}
             for r in rows], key=lambda r: r['adjusted_edge_jaccard'])[:5],
    }


if __name__ == '__main__':
    print(json.dumps(analyze(), indent=2, ensure_ascii=False))

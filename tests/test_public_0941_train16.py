"""Negative controls for the baseline's inference and validation gates."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def preflight_context(tmp_path):
    dc = '8040999a92f6b7bbd98fa8cf458141e045c0f9ad7c936bdb3b18e1f7edafe2a0'
    loaded = {'path': tmp_path / 'best.pt', 'checkpoint_epoch': 2, 'checkpoint_sha256': dc}
    env = {'BIOHUB_SECONDARY_DETECTION_WEIGHT': '0.8', 'BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT': '0.15'}
    return {
        'Path': Path, 'json': json, 'os': SimpleNamespace(environ=env),
        'WORKING_DIR': tmp_path, 'SUBMISSION_PATH': tmp_path / 'submission.csv',
        'EXPECTED_SUBMISSION_SHA': 'expected',
        '_sha256_file': lambda p: dc if p.name == 'best.pt' else 'expected',
        'DEEPCENTER_VETO_DETECTOR': loaded, 'DEEPCENTER_EXPECTED_EPOCH': 2,
        '_runtime_integrity_receipt': {
            'materialized_paths': {'deepcenter': str(loaded['path'])},
            'checkpoint_sha256': {'deepcenter': dc,
                                 'primary': '12f6881ee3620a831697ca098ff8f48e687a24225f4e048b538deec3562fe771',
                                 'secondary': '9bac2fa0dadc4a6fc1899e0caf187f4b553e0a7cd90ba1261a68b35ffe9e305f'}},
        'torch': SimpleNamespace(cuda=SimpleNamespace(device_count=lambda: 2, get_device_name=lambda i: 'Tesla T4')),
        'DET_THRESHOLD': 0.965, 'GAP_CLOSE_UM': 5.0, 'SAFE_DIV_MAX_UM': 9.0,
        'SAFE_DIV_SISTER_MAX_UM': 14.0, 'SAFE_DIV_SISTER_SYMMETRY_TAU': 0.6,
        'DEEPCENTER_SAFE_DIV_THRESHOLD': 0.25, 'MOTION_RELINK_VELOCITY_WEIGHT': 0.5,
        '_guard_report': {'configuration': {}},
    }


@pytest.mark.parametrize('fault', [None, 'submission', 'epoch', 'loaded_hash', 'loaded_path', 'parameter'])
def test_preflight_rejects_identity_drift(tmp_path, fault):
    context = preflight_context(tmp_path)
    if fault == 'submission':
        context['EXPECTED_SUBMISSION_SHA'] = 'wrong'
    elif fault == 'epoch':
        context['DEEPCENTER_VETO_DETECTOR']['checkpoint_epoch'] = 500
    elif fault == 'loaded_hash':
        context['DEEPCENTER_VETO_DETECTOR']['checkpoint_sha256'] = 'wrong'
    elif fault == 'loaded_path':
        context['DEEPCENTER_VETO_DETECTOR']['path'] = tmp_path / 'checkpoint_last.pt'
    elif fault == 'parameter':
        context['SAFE_DIV_SISTER_SYMMETRY_TAU'] = 0
    code = (ROOT / 'scripts/public_0941_train16_preflight.py').read_text(encoding='utf-8')
    if fault:
        with pytest.raises(RuntimeError, match='inference_identity_failed'):
            exec(compile(code, '<preflight>', 'exec'), context)
    else:
        exec(compile(code, '<preflight>', 'exec'), context)
        assert all(context['_inference_checks'].values())


@pytest.mark.parametrize('fault', [None, 'missing_sample', 'missing_density', 'changed_submission'])
def test_contract_is_baseline_gate_not_score_improvement_gate(tmp_path, fault):
    import math
    anchor = json.loads((ROOT / 'experiments/val_008_public_0933_train16_launchable/metrics.json').read_text())
    samples = {s: anchor['specimen_metrics'][s]['samples'] for s in ('44b6', '6bba')}
    positive = {s: anchor['specimen_metrics'][s]['division_positive_samples'] for s in samples}
    stems = sum(samples.values(), [])
    rows = [{'stem': s, 't_true': 100, 'weight': 1, 'adjusted_edge_jaccard': 0.1,
             'div_tp': 0, 'div_fp': 0, 'div_fn': 1} for s in stems]
    if fault == 'missing_sample':
        rows.pop()
    if fault == 'missing_density':
        rows[0]['t_true'] = None
    summary = {'proxy_score': 0.1, 'adjusted_edge_jaccard': 0.1, 'division_jaccard': 0, 'n_samples': len(rows)}
    context = {
        'json': json, '_contract_math': math, 'WORKING_DIR': tmp_path,
        'validator_summary_rows': [summary], 'validator_sample_rows': rows,
        'aggregate_official': lambda rows: summary, 'FROZEN_SAMPLES': samples,
        'FROZEN_POSITIVES': positive, 'division_flags': {s: s in sum(positive.values(), []) for s in stems},
        '_inference_checks': {'passed': True}, '_inference_receipt': {},
        'SUBMISSION_PATH': tmp_path / 'submission.csv', 'EXPECTED_SUBMISSION_SHA': 'expected',
        '_sha256_file': lambda p: 'wrong' if fault == 'changed_submission' else 'expected',
        'VALIDATION_STAGE_STATS': {s: {} for s in stems}, 'val_stems': stems,
        '_run_time': SimpleNamespace(perf_counter=lambda: 10), 'RUN_STARTED_AT': 0,
    }
    code = (ROOT / 'scripts/public_0941_train16_contract.py').read_text().replace(
        '__CONTROLLER_EXPERIMENT_ID__', 'val_039_public_0941_train16')
    exec(compile(code, '<contract>', 'exec'), context)
    assert context['_metrics']['metrics']['validation_contract_passed'] is (fault is None)

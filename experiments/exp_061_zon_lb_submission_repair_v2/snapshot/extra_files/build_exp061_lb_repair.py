"""Package the executed exp061 strategy for code-competition scoring, without policy edits."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.private/exp061_lb_repair/upstream/biohub-exp061-deepcenter-tta.ipynb'
OUT = ROOT / '.private/exp061_lb_repair/build/exp061_zon_lb_repair.ipynb'
EXPERIMENT = 'exp_061_zon_lb_submission_repair_v2'
IDENTITY_ANCHOR = 'from __future__ import annotations\n'
IDENTITY_LINE = "EXPERIMENT_ID = '__CONTROLLER_EXPERIMENT_ID__'  # submission adapter metadata\n"
WATCHDOG_OLD = "'experiment_id': 'exp_061_deepcenter_tta'"
WATCHDOG_NEW = "'experiment_id': EXPERIMENT_ID"
PROTOCOL_OLD = 'EXP061_VALIDATION_PROTOCOL = "public_0947_deepcenter_tta_probe_v1"'
PROTOCOL_NEW = 'EXP061_VALIDATION_PROTOCOL = "exp061_zon_submission_transport_repair_v2"'
METRIC_PROSE_OLD = (
    '"integrity gate: xyonly-arm byte-parity with the parent 0.947 submission + all "'
)
METRIC_PROSE_NEW = (
    '"integrity gate: cached xyonly byte-parity with an independent original-XY replay "'
    '\n                "on the current input + all "'
)
REFERENCE = '''    # Submission adapter: compute an independent XY reference on CURRENT input data.
    # This runs before monkeypatch installation, using the original parent heatmap.
    # The writer and tight55 configuration are identical to the cached control replay.
    _lb_reference_start = time.time()
    _lb_reference = _write_arm_submission(EXP061_CONTROL_ARM, out_dir / 'submission_parent_current.csv')
    if _lb_reference.get('budget_aborted'):
        raise RuntimeError('Current-input parent reference exceeded the existing budget')
    EXP061_PARENT_SUBMISSION_SHA256 = _lb_reference['sha256']
    (out_dir / 'current_input_reference.json').write_text(json.dumps({
        'experiment_id': experiment_id, 'sha256': EXP061_PARENT_SUBMISSION_SHA256,
        'seconds': time.time() - _lb_reference_start,
        'per_dataset_seconds': {d: seconds for (arm, d), seconds in dataset_costs.items()},
        'contract': 'Independent original-XY current-input replay; historical development hashes require separate post-run audit'
    }, allow_nan=False, indent=2))
    dataset_costs.clear()

'''
FINAL = '''# Code-competition submission adapter: all predictions come from this execution.
import hashlib as _lb_hashlib
import json as _lb_json
import os as _lb_os
import shutil as _lb_shutil
from pathlib import Path as _lb_Path

_lb_target = _lb_Path(SUBMISSION_PATH)
# Remove only the intermediate parent output; never leave it as a fallback zon submission.
if _lb_target.exists():
    _lb_target.unlink()
_exp061_telemetry = run_exp061_deepcenter_tta(globals())
_lb_metrics = _lb_json.loads((_lb_Path(WORKING_DIR) / 'metrics.json').read_text())
if not _lb_metrics.get('exp061_deepcenter_tta_integrity_passed'):
    raise RuntimeError('Refusing to submit: exp061 integrity failed')
if _exp061_telemetry['arm_status'].get('zon') != 'completed':
    raise RuntimeError('Refusing to submit: zon did not complete')
_lb_source = _lb_Path(WORKING_DIR) / 'exp061' / 'submission_zon.csv'
_lb_sha = _lb_hashlib.sha256(_lb_source.read_bytes()).hexdigest()
if _lb_sha != _lb_metrics['arm_submission_sha256']['zon']:
    raise RuntimeError('Zon output digest does not match the current-run receipt')
_lb_tmp = _lb_target.with_name(_lb_target.name + '.zon.tmp')
_lb_shutil.copyfile(_lb_source, _lb_tmp)
_lb_os.replace(_lb_tmp, _lb_target)
print('Submitted current-input zon output:', _lb_sha)
'''

def build():
    nb = json.loads(BASE.read_text(encoding='utf-8'))
    result = copy.deepcopy(nb)
    parent_code = ''.join(nb['cells'][2]['source'])
    assert parent_code.count(IDENTITY_ANCHOR) == 1
    assert parent_code.count(WATCHDOG_OLD) == 1
    result['cells'][2]['source'] = parent_code.replace(IDENTITY_ANCHOR, IDENTITY_ANCHOR + IDENTITY_LINE).replace(WATCHDOG_OLD, WATCHDOG_NEW).splitlines(True)
    module = ''.join(nb['cells'][3]['source'])
    anchor = '    # -- install patches -------------------------------------------------------\n'
    assert module.count(anchor) == 1
    assert module.count(METRIC_PROSE_OLD) == 1
    assert module.count(PROTOCOL_OLD) == 1
    adapted_module = module.replace(METRIC_PROSE_OLD, METRIC_PROSE_NEW).replace(
        PROTOCOL_OLD, PROTOCOL_NEW
    )
    result['cells'][3]['source'] = adapted_module.replace(anchor, REFERENCE + anchor).splitlines(True)
    result['cells'][4]['source'] = FINAL.splitlines(True)
    # Exact source equality for every inference/configuration cell and for the TTA
    # module after removing the current-input reference adapter.
    assert result['cells'][:2] == nb['cells'][:2]
    assert ''.join(result['cells'][2]['source']).replace(IDENTITY_LINE, '').replace(WATCHDOG_NEW, WATCHDOG_OLD) == parent_code
    assert ''.join(result['cells'][3]['source']).replace(REFERENCE, '').replace(
        METRIC_PROSE_NEW, METRIC_PROSE_OLD
    ).replace(PROTOCOL_NEW, PROTOCOL_OLD) == module
    for i, cell in enumerate(result['cells']):
        if cell['cell_type'] == 'code':
            compile(''.join(cell['source']), f'cell_{i}', 'exec')
            cell['outputs'] = []
            cell['execution_count'] = None
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding='utf-8')
    dependency_paths = [
        BASE,
        ROOT / 'scripts/build_exp061_lb_repair.py',
        ROOT / 'scripts/validate_exp061_lb_repair.py',
        ROOT / 'scripts/test_exp061_behavioral.py',
        ROOT / 'scripts/exp061_deepcenter_tta.py',
    ]
    dependency_sha256 = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in dependency_paths
    }
    receipt = {'base_sha256': hashlib.sha256(BASE.read_bytes()).hexdigest(),
               'notebook_sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(),
               'dependency_sha256': dependency_sha256,
               'inference_unchanged_except_experiment_identity': True,
               'tta_module_unchanged_except_input_parity_adapter_and_validation_prose': True}
    (OUT.parent / 'build-receipt.json').write_text(json.dumps(receipt, indent=2))
    import yaml
    config = yaml.safe_load((ROOT / 'configs/exp_061_deepcenter_tta.yaml').read_text())
    config.update(experiment_id=EXPERIMENT, parent='exp_061_deepcenter_tta',
        source_notebook=OUT.relative_to(ROOT).as_posix(),
        hypothesis='A full current-input exp061 zon inference notebook fixes the static-CSV code-submission failure without changing the inference strategy.',
        change={'component': 'code_submission_adapter', 'from': 'Static development CSV promotion and fixed development parity hash',
                'to': 'Full unchanged exp061 inference, original-XY current-input parity, fail-closed current-run zon publication',
                'variables_changed': 'Submission transport and input-relative validation only; no prediction policy edits'},
        authorization={'scope': 'User requested diagnosis, submission-only repair and resubmission; no algorithm strategy changes. Existing exp061 strategy CONSENSUS retained. Fresh admission PASS, smoke and 2h reservation required.'})
    config['provenance']['submission_repair'] = 'docs/research/exp061_lb_submission_repair.md'
    config['validation']['protocol'] = 'exp061_zon_submission_transport_repair_v2'
    config['validation']['warning'] = ('Integrity only: cached xyonly must match an independent original-XY replay on current input; '
        'all existing graph/config/cache/finite/budget gates retained. Full development-run output must additionally '
        'match historical xyonly d34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60 and '
        'zon 2593a5438a17e5649736fcd6ad2f7af4c2fa8f822a759e9f51d877cdf6c840a1 before LB submission. '
        'Historical CSV hashes do not apply to hidden scoring input. No quality inference from this gate.')
    config['substrate_note'] = ('Full unchanged executed exp061 inference; only experiment identity, current-input '
        'reference validation and fail-closed zon output publication are adapted. Three arms and all policies remain frozen. '
        'Additional original-XY replay is timed separately within the existing two-hour watchdog.')
    config['provenance']['builder'] = 'scripts/build_exp061_lb_repair.py'
    config['provenance']['repair_upstream_notebook'] = BASE.relative_to(ROOT).as_posix()
    config['provenance']['repair_dependency_sha256'] = dependency_sha256
    config['provenance'].pop('expected_parent_submission_sha256', None)
    config['provenance']['historical_development_xyonly_submission_sha256'] = (
        'd34533806b3153ddd4f33f3bbc1dea70af2d5406bb1ea48e42c135a97c213f60'
    )
    config['provenance']['historical_development_zon_submission_sha256'] = (
        '2593a5438a17e5649736fcd6ad2f7af4c2fa8f822a759e9f51d877cdf6c840a1'
    )
    config['submission']['user_authorized_count'] = 1
    config['kaggle'].update(slug='biohub-exp061-zon-lb-repair', title='biohub-exp061-zon-lb-repair',
        extra_files=['scripts/build_exp061_lb_repair.py', 'scripts/validate_exp061_lb_repair.py',
                     'scripts/test_exp061_behavioral.py', 'scripts/exp061_deepcenter_tta.py',
                     BASE.relative_to(ROOT).as_posix()])
    config['local']['smoke_test'] = ['{python}', 'scripts/validate_exp061_lb_repair.py', '{source_notebook}']
    (ROOT / 'configs' / (EXPERIMENT + '.yaml')).write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    build()

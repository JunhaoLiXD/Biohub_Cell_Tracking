"""Package the executed exp061 strategy for code-competition scoring, without policy edits."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / '.private/exp061_lb_repair/upstream/biohub-exp061-deepcenter-tta.ipynb'
OUT = ROOT / '.private/exp061_lb_repair/build/exp061_zon_lb_repair.ipynb'
EXPERIMENT = 'exp_061_zon_lb_submission_repair'
REFERENCE = '''    # Submission adapter: compute an independent XY reference on CURRENT input data.
    # This runs before monkeypatch installation, using the original parent heatmap.
    # The writer and tight55 configuration are identical to the cached control replay.
    _lb_reference = _write_arm_submission(EXP061_CONTROL_ARM, out_dir / 'submission_parent_current.csv')
    if _lb_reference.get('budget_aborted'):
        raise RuntimeError('Current-input parent reference exceeded the existing budget')
    EXP061_PARENT_SUBMISSION_SHA256 = _lb_reference['sha256']
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
    module = ''.join(nb['cells'][3]['source'])
    anchor = '    # -- install patches -------------------------------------------------------\n'
    assert module.count(anchor) == 1
    result['cells'][3]['source'] = module.replace(anchor, REFERENCE + anchor).splitlines(True)
    result['cells'][4]['source'] = FINAL.splitlines(True)
    # Exact source equality for every inference/configuration cell and for the TTA
    # module after removing the current-input reference adapter.
    assert result['cells'][:3] == nb['cells'][:3]
    assert ''.join(result['cells'][3]['source']).replace(REFERENCE, '') == module
    for i, cell in enumerate(result['cells']):
        if cell['cell_type'] == 'code':
            compile(''.join(cell['source']), f'cell_{i}', 'exec')
            cell['outputs'] = []
            cell['execution_count'] = None
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding='utf-8')
    receipt = {'base_sha256': hashlib.sha256(BASE.read_bytes()).hexdigest(),
               'notebook_sha256': hashlib.sha256(OUT.read_bytes()).hexdigest(),
               'inference_cells_unchanged': True, 'tta_module_unchanged_except_input_parity_adapter': True}
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
    config['provenance']['builder'] = 'scripts/build_exp061_lb_repair.py'
    config['submission']['user_authorized_count'] = 1
    config['kaggle'].update(slug='biohub-exp061-zon-lb-repair', title='biohub-exp061-zon-lb-repair',
        extra_files=['scripts/build_exp061_lb_repair.py', 'scripts/validate_exp061_lb_repair.py'])
    config['local']['smoke_test'] = ['{python}', 'scripts/validate_exp061_lb_repair.py', '{source_notebook}']
    (ROOT / 'configs' / (EXPERIMENT + '.yaml')).write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    build()

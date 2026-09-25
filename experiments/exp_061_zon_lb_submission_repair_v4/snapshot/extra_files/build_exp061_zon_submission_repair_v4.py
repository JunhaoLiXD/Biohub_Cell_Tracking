"""Build a versioned zon submission notebook with the watchdog armed through publication."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PARENT_NB = ROOT / 'experiments/exp_061_zon_lb_submission_repair_v3/snapshot/source/exp061_zon_submission_repair_v3.ipynb'
PARENT_MODULE = ROOT / 'experiments/exp_061_zon_lb_submission_repair_v3/snapshot/extra_files/exp061_zon_deployment.py'
OUT_MODULE = ROOT / 'scripts/exp061_zon_deployment_v4.py'
OUT_NB = ROOT / '.private/exp061_lb_repair_v4/build/exp061_zon_submission_repair_v4.ipynb'
OUT_CONFIG = ROOT / 'configs/exp_061_zon_lb_submission_repair_v4.yaml'
EXPERIMENT = 'exp_061_zon_lb_submission_repair_v4'
EXPECTED_NB = '8efd5500fc80909928679d6dbc5e4361a28374ec214e57bf53cce0239f5cfaba'
EXPECTED_MODULE = '35aa6d61c543a891da5649ed48722938e10b4ca240a31d3c3e4360c3ccd39123'

def replace_exact(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f'expected one occurrence of {old[:80]!r}, got {text.count(old)}')
    return text.replace(old, new, 1)

def build() -> None:
    parent_bytes = PARENT_NB.read_bytes()
    module_bytes = PARENT_MODULE.read_bytes()
    if hashlib.sha256(parent_bytes).hexdigest() != EXPECTED_NB:
        raise RuntimeError('v3 immutable notebook identity changed')
    if hashlib.sha256(module_bytes).hexdigest() != EXPECTED_MODULE:
        raise RuntimeError('v3 immutable deployment module identity changed')
    nb = copy.deepcopy(json.loads(parent_bytes.decode('utf-8')))
    module = module_bytes.decode('utf-8')
    module = replace_exact(module, 'EXP061_EXPERIMENT_ID = "exp_061_zon_lb_submission_repair_v3"',
                           'EXP061_EXPERIMENT_ID = "exp_061_zon_lb_submission_repair_v4"')
    module = replace_exact(module, 'EXP061_VALIDATION_PROTOCOL = "exp061_zon_only_deployment_v3"',
                           'EXP061_VALIDATION_PROTOCOL = "exp061_zon_only_deployment_v4"')
    module = replace_exact(module, '    _disarm_watchdog()\n    return telemetry',
                           '    # Keep the whole-run watchdog armed through final CSV audit and publication.\n    return telemetry')
    compile(module, 'exp061_zon_deployment_v4.py', 'exec')
    final = ''.join(nb['cells'][4]['source'])
    old = '_zon_os.replace(_zon_tmp, _zon_target)\nprint("Published current-run zon submission:", _zon_digest)'
    new = '''import time as _zon_time
if _zon_time.time() - float(_EXP061_RUN_START) >= float(EXP061_HARD_STOP_SECONDS):
    _zon_tmp.unlink(missing_ok=True)
    raise RuntimeError("Refusing publication: whole-notebook deadline reached before atomic replace")
_zon_os.replace(_zon_tmp, _zon_target)
import signal as _zon_signal
if hasattr(_zon_signal, "SIGALRM"):
    _zon_signal.alarm(0)
print("Published current-run zon submission:", _zon_digest)'''
    final = replace_exact(final, old, new)
    compile(final, 'v4_final_cell', 'exec')
    nb['cells'][3]['source'] = module.splitlines(True)
    nb['cells'][4]['source'] = final.splitlines(True)
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            cell['outputs'] = []
            cell['execution_count'] = None
    if nb['cells'][:3] != json.loads(parent_bytes.decode('utf-8'))['cells'][:3]:
        raise RuntimeError('v3 parent inference/setup cells changed')
    OUT_NB.parent.mkdir(parents=True, exist_ok=True)
    OUT_MODULE.write_text(module, encoding='utf-8', newline='\n')
    OUT_NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding='utf-8', newline='\n')
    config = yaml.safe_load((ROOT / 'configs/exp_061_zon_lb_submission_repair_v3.yaml').read_text(encoding='utf-8'))
    config['experiment_id'] = EXPERIMENT
    config['parent'] = 'exp_061_zon_lb_submission_repair_v2'
    config['source_notebook'] = OUT_NB.relative_to(ROOT).as_posix()
    config['hypothesis'] = ('A zon-only deployment with the frozen prediction policy and a watchdog armed through final publication '
                            'can complete the current-input output contract; the v2 hidden failure cause remains unknown.')
    config['change'] = {'component': 'zon_only_submission_transport_v4',
                        'from': 'v2 full research replay; v3 unlaunched attempt disarmed watchdog before final publication',
                        'to': 'one zon replay and a watchdog retained until atomic publication',
                        'variables_changed': 'deployment execution and validation only; frozen zon prediction policy'}
    config['validation']['protocol'] = 'exp061_zon_only_deployment_v4'
    config['validation']['warning'] = ('Deployment integrity only, not a quality metric. The v2 hidden traceback is unavailable. '
                                       'The 2h watchdog covers parent inference, zon replay, final audit, staging, and publication. '
                                       'No leaderboard submission is authorized.')
    config['substrate_note'] = ('Unchanged v3 parent inference cells and frozen zon prediction/graph-writer policy. '
                                'The sole behavioral correction from v3 is keeping the 2h watchdog armed through final publication.')
    config['provenance']['source_parent'] = 'exp_061_zon_lb_submission_repair_v3 (unlaunched blocked snapshot)'
    config['provenance']['strategy_amendment'] = 'experiments/exp_061_zon_lb_submission_repair_v4/strategy_amendment_v1.md'
    config['provenance']['expected_v3_notebook_sha256'] = EXPECTED_NB
    config['provenance']['expected_v3_module_sha256'] = EXPECTED_MODULE
    config['provenance']['generated_zon_deployment_sha256'] = hashlib.sha256(OUT_MODULE.read_bytes()).hexdigest()
    config['kaggle']['slug'] = 'biohub-exp061-zon-deploy-v4'
    config['kaggle']['title'] = 'biohub-exp061-zon-deploy-v4'
    config['kaggle']['extra_files'] = [
        'scripts/build_exp061_zon_submission_repair_v4.py',
        'scripts/exp061_zon_deployment_v4.py',
        'scripts/validate_exp061_zon_deployment_v4.py',
        PARENT_NB.relative_to(ROOT).as_posix(),
        PARENT_MODULE.relative_to(ROOT).as_posix(),
    ]
    config['local']['smoke_test'] = ['{python}', 'scripts/validate_exp061_zon_deployment_v4.py', '{source_notebook}']
    OUT_CONFIG.write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
    receipt = {'parent_notebook_sha256': EXPECTED_NB, 'parent_module_sha256': EXPECTED_MODULE,
               'module_sha256': hashlib.sha256(OUT_MODULE.read_bytes()).hexdigest(),
               'notebook_sha256': hashlib.sha256(OUT_NB.read_bytes()).hexdigest(),
               'watchdog_disarm_after_publication': True}
    (OUT_NB.parent / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))

if __name__ == '__main__':
    build()


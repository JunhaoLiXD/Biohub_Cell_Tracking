"""Add isolated guards and create controller config for the existing ep015 vehicle."""
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
FINAL = '_exp068_metrics = exp068_finalize(globals())\n(WORKING_DIR / "metrics.json").write_text(json.dumps(_exp068_metrics, indent=2) + "\\n")\n'
WATCHDOG = '''# Same bounded-process watchdog used by exp067 export; no status polling.
import os, time, threading, psutil
_exp068_started = time.monotonic()
def _exp068_timeout():
    time.sleep(5400)
    print("EXP068 HARD WALLTIME: 5400 seconds", flush=True)
    for _child in psutil.Process(os.getpid()).children(recursive=True):
        try: _child.kill()
        except psutil.Error: pass
    os._exit(124)
threading.Thread(target=_exp068_timeout, daemon=True).start()
'''


def add_contract(nb):
    contract = (ROOT / 'scripts/exp068_contract.py').read_text(encoding='utf-8')
    c5 = ''.join(nb['cells'][5]['source'])
    anchor = '    write_test_submission("base")'
    assert c5.count(anchor) == 1
    c5 = contract + '\n\n' + c5.replace(anchor, '    exp068_preflight(globals())\n' + anchor)
    nb['cells'][5]['source'] = c5.splitlines(keepends=True)
    nb['cells'].insert(0, {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': WATCHDOG.splitlines(keepends=True)})
    nb['cells'].append({'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': FINAL.splitlines(keepends=True)})
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            compile(''.join(cell['source']), f'<exp068_cell_{i}>', 'exec')
            cell['outputs'], cell['execution_count'] = [], None
    return nb


def write_config():
    parent = yaml.safe_load((ROOT / 'configs/exp_064_x138_verbatim_repro.yaml').read_text(encoding='utf-8'))
    kaggle = {k: v for k, v in parent['kaggle'].items() if k != 'note'}
    kaggle.update(slug='biohub-exp068-ep015', title='biohub-exp068-ep015', extra_files=[
        'scripts/build_exp068_probe.py', 'scripts/exp068_build_support.py', 'scripts/exp068_contract.py',
        'scripts/smoke_exp068.py', 'scripts/audit_exp068_collection.py'])
    config = {'schema_version': 1, 'experiment_id': 'exp_068_ep015_single_probe',
              'parent': 'exp_064_x138_verbatim_repro',
              'hypothesis': 'A fixed output edge-probability floor 0.15 on the exp064-compatible vehicle improves recorded Public LB from 0.953 to at least 0.954 at displayed precision.',
              'change': {'component': 'output_edge_probability_floor', 'from': 0., 'to': .15,
                         'exact': 'Same verified vehicle as exp066 cx03, but cx03 OFF and ep015 ON. Validator/sweep OFF, all other new levers OFF. Existing summary typo fix, auto-attach refusal and arm snapshot retained. Add prediction-neutral pre-write/final configuration and dependency assertions, output graph audit/metrics contract and 5400s process watchdog. No training, no alternative prediction algorithm.'},
              'source_notebook': 'scratchpad/exp068_build/biohub-exp068-ep015.ipynb',
              'strategy_record': 'docs/research/ep015_continuation_2026-09-26/strategy_consensus_v1.md',
              'execution_authorization': 'User accepted one ep015 run and one LB probe plus CPU diagnostic; no promotion or second attempt.',
              'validation': {'protocol': 'ep015_single_probe_v1', 'primary_metric': 'ep015_probe_integrity_passed',
                             'limitations': 'Engineering gate only. Existing 8-movie/2-prefix proxy is reused exploratory evidence, not independent validation; worst prefix regression about 0.0085. LB is unknown. Exact graph hashes across different ep thresholds have not been established.'},
              'admission': {'require_codex_review': True, 'reviewer_provider': 'codex'},
              'local': {'smoke_test': ['{python}', 'scripts/smoke_exp068.py', '{source_notebook}']},
              'budget': {'tier': 1, 'expected_gpu_hours': 2., 'note': 'Expected ~0.5h, planned reservation 2h; watchdog kills descendants and kernel at 5400 seconds from first cell. Platform startup is outside timer. No polling/retry; identical hidden-run timeout accepted as a failure risk.'},
              'success': {'minimum_improvement': 0., 'regression_threshold': 0.},
              'evaluation': {'mode': 'gate', 'gate_field': 'ep015_probe_integrity_passed'},
              'kaggle': kaggle,
              'leaderboard': {'authorized': True, 'max_submissions': 1, 'daily_cap': 3,
                              'rule': 'One only after current-output independent audit and authenticated remote cap/duplicate check. >=0.954 exploratory displayed gain, 0.953 registered null, <=0.952 reject. Keep 56535761 selected regardless; no automatic re-selection.'},
              'stop_rule': 'Any snapshot/config/identity/graph/degradation failure or duplicate output stops. Wait for user completion, collect once; no training, retry, second probe or public push.'}
    (ROOT / 'configs/exp_068_ep015_single_probe.yaml').write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')


if __name__ == '__main__':
    write_config()

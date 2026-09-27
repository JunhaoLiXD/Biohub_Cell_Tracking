"""CPU smoke of the actual frozen notebook: source parity, guards and pruning behavior."""
import ast
import copy
import csv
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import exp068_contract as contract
from scripts.exp068_build_support import WATCHDOG, FINAL
from experiment_controller.core import validate_notebook


def must_reject(fn):
    try:
        fn()
    except (AssertionError, KeyError, ValueError):
        return
    raise AssertionError('Invalid fixture was accepted')


def main():
    path = Path(sys.argv[1])
    validate_notebook(path, require_metrics_contract=True)
    nb = json.loads(path.read_text(encoding='utf-8'))
    old_path = ROOT / 'experiments/exp_066_probe_cx03/kaggle_kernel/biohub-exp066-cx03.ipynb'
    old = json.loads(old_path.read_text(encoding='utf-8'))
    assert len(nb['cells']) == len(old['cells']) + 2
    assert ''.join(nb['cells'][0]['source']) == WATCHDOG
    assert ''.join(nb['cells'][-1]['source']) == FINAL
    embedded = (ROOT / 'scripts/exp068_contract.py').read_text(encoding='utf-8')
    for i, before in enumerate(old['cells']):
        after = ''.join(nb['cells'][i + 1]['source'])
        if i == 5:
            assert after.startswith(embedded + '\n\n')
            after = after[len(embedded) + 2:]
            assert after.count('    exp068_preflight(globals())\n') == 1
            after = after.replace('    exp068_preflight(globals())\n', '')
        after = after.replace('exp_068', 'exp_066')
        expected = ''.join(before['source'])
        if i == 0:
            for key, value in [('BIOHUB_OUTPUT_MIN_EDGE_PROB', '0.15'), ('BIOHUB_COUNT_EXCESS_FRAC', '0.0')]:
                new_lines = [s for s in after.splitlines() if s.startswith(f'os.environ["{key}"] =')]
                old_lines = [s for s in expected.splitlines() if s.startswith(f'os.environ["{key}"] =')]
                assert len(new_lines) == len(old_lines) == 1
                assert new_lines[0].startswith(f'os.environ["{key}"] = "{value}"')
                after = after.replace(new_lines[0], old_lines[0])
        assert after == expected, f'Unexpected predictor/vehicle source delta in original cell {i}'

    # Exercise the EXACT archived filter function extracted from the frozen notebook.
    tree = ast.parse(''.join(nb['cells'][6]['source']))
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'filter_weak_edges')
    ns = {'np': SimpleNamespace(isfinite=math.isfinite), 'OUTPUT_MIN_EDGE_PROB': .15}
    exec(compile(ast.Module(body=[func], type_ignores=[]), '<frozen-filter>', 'exec'), ns)
    nodes = {0: {'t': 0}, 1: {'t': 1}, 2: {'t': 2}, 3: {'t': 1}, 4: {'t': 2}}
    edges = [{'source_id': 0, 'target_id': 1, 'edge_prob': .149},
             {'source_id': 1, 'target_id': 2, 'edge_prob': .1},
             {'source_id': 0, 'target_id': 3, 'edge_prob': .15},
             {'source_id': 3, 'target_id': 4, 'edge_prob': None}]
    stats = {'weak_edge_dropped': 0, 'weak_edge_orphan_nodes': 0}
    kept, links = ns['filter_weak_edges'](copy.deepcopy(nodes), copy.deepcopy(edges), stats)
    assert stats == {'weak_edge_dropped': 2, 'weak_edge_orphan_nodes': 1}
    assert set(kept) == {0, 2, 3, 4} and links == edges[2:]
    ns['OUTPUT_MIN_EDGE_PROB'] = 0.
    assert ns['filter_weak_edges'](nodes, edges, {'weak_edge_dropped': 0}) == (nodes, edges)

    with tempfile.TemporaryDirectory(prefix='exp068_smoke_') as td:
        root = Path(td)
        receipt = {'checkpoint_sha256': contract.EXP068_CHECKPOINTS,
                   'support_repo_python_manifest_sha256': '978b626d1fd1e7397435a437dfe68691defe1572fc3c20e61012d7c9b52ed029'}
        (root / 'runtime_integrity.json').write_text(json.dumps(receipt))
        context = dict(contract.EXP068_EXPECTED, WORKING_DIR=root, _V9_AUTO_SET_ENV={}, FROZEN_PRESET_OVERRIDES=None)
        saved = dict(os.environ)
        try:
            for key, value in contract.EXP068_EXPECTED.items():
                os.environ['BIOHUB_' + key] = str(value)
            os.environ['BIOHUB_VALIDATOR_ENABLE'] = '0'
            contract.exp068_preflight(context)
            for key in contract.EXP068_EXPECTED:
                bad = dict(context, **{key: .9})
                must_reject(lambda: contract.exp068_preflight(bad))
            must_reject(lambda: contract.exp068_preflight(dict(context, _V9_AUTO_SET_ENV={'preset': 'bad'})))
            must_reject(lambda: contract.exp068_preflight(dict(context, FROZEN_PRESET_OVERRIDES={})))
            os.environ['BIOHUB_VALIDATOR_ENABLE'] = '1'
            must_reject(lambda: contract.exp068_preflight(context))
        finally:
            os.environ.clear()
            os.environ.update(saved)
        header = ['id','dataset','row_type','node_id','t','z','y','x','source_id','target_id']
        rows = [[0,'test','node',0,0,1,1,1,-1,-1], [1,'test','node',1,1,1,1,1,-1,-1],
                [2,'test','edge',-1,-1,-1,-1,-1,0,1]]
        def check_csv(values, discover=['test']):
            file = root / 'submission.csv'
            with file.open('w', newline='') as fh:
                writer = csv.writer(fh); writer.writerow(header); writer.writerows(values)
            return contract.exp068_audit_csv(file, discover)
        assert check_csv(rows)['test']['edges'] == 1
        bad = copy.deepcopy(rows); bad[-1][-1] = 9
        must_reject(lambda: check_csv(bad))
        must_reject(lambda: check_csv(rows, ['test', 'missing']))
        bad = copy.deepcopy(rows); bad[1][4] = 0
        must_reject(lambda: check_csv(bad))
    print('PASS: exact vehicle delta, embedded contract, all code syntax, threshold/boundary/orphan behavior, config drift and graph-negative fixtures.')


if __name__ == '__main__':
    main()

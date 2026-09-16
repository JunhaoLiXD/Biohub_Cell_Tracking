"""Build fixed original-score successor; never launch or change admission gates."""
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / 'experiments/diag_051_public_0942_tracklet_evidence/snapshot/source/public_0942_tracklet_evidence.ipynb'
TARGET = ROOT / '.private/current/original_score_joint_repair.ipynb'
EXPERIMENT = 'exp_053_original_score_joint_repair'
SOLVER_NUMPY_IMPORT = ''
SOLVER_NUMPY_NAME = 'np'


def once(s, old, new):
    assert s.count(old) == 1, old[:100]
    return s.replace(old, new, 1)


def graph_hash(path):
    v = json.loads(gzip.decompress(path.read_bytes()))
    p = dict(pred_nodes=v['pred_nodes'], pred_edges=v['pred_edges'])
    return hashlib.sha256(json.dumps(p, sort_keys=True, allow_nan=False).encode()).hexdigest()


def build():
    nb = json.loads(PARENT.read_text(encoding='utf-8'))
    nb['cells'][0]['source'] = ['# Original-score joint association repair\n\n',
        'Behavior parent: repro_041_public_0941_motion_ema. Evidence donor: diag_051. ',
        'Frozen original-score control from local_052 attempt02; five-frame context remains rejected. ',
        'No training, parameter sweep, leaderboard submission or promotion. ',
        'This notebook requires fresh review, smoke and budget admission before execution.\n']
    core = (ROOT / 'scripts/original_score_joint_repair.py').read_text()
    hooks = (ROOT / 'scripts/original_score_joint_hooks.py').read_text()
    install = ('import types as _jr_types\nimport sys as _jr_sys\n'
               '_jr_module = _jr_types.ModuleType("_original_joint")\n'
               '_jr_sys.modules[_jr_module.__name__] = _jr_module\n'
               f'exec(compile({core!r}, "<original-score-repair>", "exec"), _jr_module.__dict__)\n'
               )
    dependency = ROOT / '.private/runtime/joint_repair_linux'
    manifest = json.loads((dependency / 'manifest.json').read_text())
    binary = (dependency / manifest['extension']).read_bytes()
    assert hashlib.sha256(binary).hexdigest() == manifest['extension_sha256']
    install += (SOLVER_NUMPY_IMPORT +
                'import base64 as _jr_b64\nimport hashlib as _jr_hashlib\n'
                'import importlib.util as _jr_import\n'
                f'_jr_binary = _jr_b64.b64decode({base64.b64encode(binary).decode()!r})\n'
                f'assert _jr_hashlib.sha256(_jr_binary).hexdigest() == {manifest["extension_sha256"]!r}\n'
                f'_jr_path = WORKING_DIR / {manifest["extension"]!r}\n'
                '_jr_path.write_bytes(_jr_binary)\n'
                f'(WORKING_DIR / "JOINT_SOLVER_LICENSE.txt").write_text({(dependency / "SCIPY_LICENSE.txt").read_text()!r})\n'
                '_jr_spec = _jr_import.spec_from_file_location("_lsap", _jr_path)\n'
                '_jr_lsap = _jr_import.module_from_spec(_jr_spec)\n'
                '_jr_spec.loader.exec_module(_jr_lsap)\n'
                '_jr_module.linear_sum_assignment = _jr_lsap.linear_sum_assignment\n'
                '_jr_solver_version = "1.18.1"\n'
                f'_jr_r, _jr_c = _jr_module.linear_sum_assignment({SOLVER_NUMPY_NAME}.array([[1., 3.], [4., 1.]]), maximize=True)\n'
                'assert _jr_r.tolist() == [0, 1] and _jr_c.tolist() == [1, 0]\n')
    for c in nb['cells']:
        if c['cell_type'] != 'code':
            continue
        s = ''.join(c['source'])
        if 'def list_test_stems()' in s:
            s = once(s, "os.environ['BIOHUB_TRACKLET_EVIDENCE'] = 'off'",
                     "os.environ['BIOHUB_TRACKLET_EVIDENCE'] = 'validation'")
            # Pin solver before model inference starts.
            s = install + '\n' + s
        if 'def filter_output_graph(' in s:
            s = hooks + '\n' + s
            s = once(s, 'def _ev_graph(stem, stage, nodes, edges):\n',
                     'def _ev_graph(stem, stage, nodes, edges):\n    _jr_observe(stem, nodes)\n')
            s = once(s, '    edges: list[dict[str, object]] = []\n    for edge in raw_edges:',
                     '    _jr_begin(dataset, nodes_by_id)\n    edges: list[dict[str, object]] = []\n    for edge in raw_edges:')
            anchor = '    nodes_by_id = linefit_smooth_output_graph(nodes_by_id, edges, stats)\n'
            s = once(s, anchor, anchor + '    edges = _jr_finish(dataset, nodes_by_id, edges)\n')
        if 'REPRO_EXPECTED = ' in s:
            # Reuse frozen validation/inference contract construction, not old quality gates.
            s = s.split('REPRO_EXPECTED = ', 1)[0]
            for old, new in [('0.9359778132422281', '0.9387332376874039'),
                             ('0.9217996822478786', '0.9228460029238004'),
                             ('0.9017996822478785', '0.9028460029238004'),
                             ('0.9403315937448887', '0.9442148231081169'),
                             ('0.9221497755630705', '0.9242148231081169')]:
                s = s.replace(old, new)
            s = s.replace('"diag_051_public_0942_tracklet_evidence"', repr(EXPERIMENT))
            ref = ROOT / 'experiments/local_052_joint_graph_pilot_v1_attempt02'
            result = json.loads((ref / 'result.json').read_text())
            expected = {stem: dict(input=graph_hash(ref/'artifacts'/(stem+'_no_change.json.gz')),
                                   output=graph_hash(ref/'artifacts'/(stem+'_original_score.json.gz')),
                                   score=rec['arms']['original_score']['score'])
                        for stem, rec in result['videos'].items()}
            s += '\nJR_EXPECTED = ' + repr(expected) + '\n'
            s += (ROOT / 'scripts/original_score_joint_contract.py').read_text()
        if '_inference_receipt = {' in s:
            s = s.replace('"parent": "val_039_public_0941_train16"',
                          '"parent": "repro_041_public_0941_motion_ema"')
            s = s.replace('"change": "motion_relink_velocity_estimator_only"',
                          '"change": "fixed_original_score_joint_repair_after_smoothing"')
        c['source'] = s.splitlines(keepends=True)
        c.update(outputs=[], execution_count=None)
        ast.parse(s)
    TARGET.write_text(json.dumps(nb, indent=1)+'\n', encoding='utf-8')
    return TARGET


if __name__ == '__main__':
    print(build())

"""Freeze the first bounded exp067 Kaggle feature-export attempt; never launch it."""
import json
import ast
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.exp067.patching import patch_notebook, patch_predictor, replay_parent, parent_notebook


def main():
    dev = ROOT / 'experiments/exp_067_temporal_joint_lineage'
    split = {'protocol': 'leave_one_movie_out',
             'train': ['44b6_12dfb391', '44b6_267148e4', '44b6_2a2eff9f',
                       '6bba_062c8d37', '6bba_07e24132', '6bba_085bf656'],
             'holdout': ['44b6_341df25f', '6bba_09961292'],
             'test_stems': ['44b6_0113de3b', '44b6_0b24845f', '6bba_05b6850b', '6bba_05db0fb1']}
    (dev / 'splits_v1.json').write_text(json.dumps(split, indent=2), encoding='utf-8')
    compile(patch_predictor(replay_parent()), '<actual patched predictor>', 'exec')
    nb = patch_notebook('export', split['train'] + split['holdout'])
    watchdog = '''# Bound this first export attempt, including child predictor processes.
import os, time, threading, psutil
_exp067_started = time.monotonic()
def _exp067_timeout():
    time.sleep(5400)
    print("EXP067 HARD WALLTIME: 5400 seconds; stopping this attempt", flush=True)
    for _child in psutil.Process(os.getpid()).children(recursive=True):
        try: _child.kill()
        except psutil.Error: pass
    os._exit(124)
threading.Thread(target=_exp067_timeout, daemon=True).start()
'''
    nb['cells'].insert(1, {'cell_type': 'code', 'metadata': {}, 'execution_count': None,
                           'outputs': [], 'source': watchdog})
    parent_receipt = json.loads((ROOT / 'experiments/exp_064_x138_verbatim_repro/collection/bidirectional_production_runtime_integrity.json').read_text())
    expected_env = {}
    for node in ast.parse(''.join(parent_notebook()['cells'][0]['source'])).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Subscript) and ast.unparse(target.value) == 'os.environ':
                if ast.literal_eval(target.slice) == 'BIOHUB_KERNEL_START_TS':
                    continue  # wall clock is recorded, not a frozen model configuration
                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'str':
                    value = str(ast.literal_eval(node.value.args[0]))
                else:
                    value = ast.literal_eval(node.value)
                expected_env[ast.literal_eval(target.slice)] = value
    expected_env['BIOHUB_VALIDATOR_ENABLE'] = '1'
    dependency_gate = f'''# Runtime dependency/configuration gate before TRAIN inference.
import hashlib
_x67_expected_checkpoints = {parent_receipt['checkpoint_sha256']!r}
assert _runtime_integrity_receipt["checkpoint_sha256"] == _x67_expected_checkpoints
assert _runtime_integrity_receipt["support_repo_python_manifest_sha256"] == {parent_receipt['support_repo_python_manifest_sha256']!r}
_x67_head_sha = hashlib.sha256(Path(os.environ["V1284_HEAD"]).read_bytes()).hexdigest()
assert _x67_head_sha == "625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c"
_x67_expected_env = {expected_env!r}
_x67_env_mismatch = {{k: (v, os.environ.get(k)) for k, v in _x67_expected_env.items() if os.environ.get(k) != v}}
assert not _x67_env_mismatch, _x67_env_mismatch
'''
    # Original cell4 is index6 after the two bootstrap cells; inference is skipped there.
    nb['cells'].insert(7, {'cell_type': 'code', 'metadata': {}, 'execution_count': None,
                           'outputs': [], 'source': dependency_gate})
    final = '''# Structured engineering gate: exported artifacts, not an accuracy claim.
import hashlib, json, platform, copy
from scripts.exp067 import provenance as _p67, supervise as _s67
_x67rt.raise_if_fatal()
_rows67 = []
_dir67 = Path(os.environ["BIOHUB_EXP067_EXPORT_DIR"])
_parity67 = []
# Representative control: same raw graphs, hooks disabled; no repeated detector inference.
_saved_test67 = TEST_DIR
_saved_export67 = os.environ["BIOHUB_EXP067_EXPORT"]
try:
    globals()["TEST_DIR"] = TRAIN_DIR
    os.environ["BIOHUB_EXP067_EXPORT"] = "0"
    for _prefix67 in ("44b6", "6bba"):
        _stem67 = next(s for s in _x67_stems if s.startswith(_prefix67 + "_"))
        _raw_n67, _raw_e67 = VAL_RAW_GRAPHS[_stem67]
        _control_n67, _control_e67, _ = filter_output_graph(copy.deepcopy(_raw_n67), copy.deepcopy(_raw_e67),
            dataset=_stem67, deepcenter_bundle=globals().get("DEEPCENTER_VETO_DETECTOR"))
        _graph67 = _p67.load_final_graph(_dir67 / f"{_stem67}.final.npz")
        assert set(_control_n67) == set(_graph67.node_id.tolist())
        for _id67, _t67, _xyz67 in zip(_graph67.node_id, _graph67.node_t, _graph67.node_zyx):
            _node67 = _control_n67[int(_id67)]
            assert (_node67["t"], _node67["z"], _node67["y"], _node67["x"]) == (int(_t67), *map(float, _xyz67))
        assert {(int(e["source_id"]), int(e["target_id"])) for e in _control_e67} == _graph67.parent_edge_set()
        _parity67.append({"stem": _stem67, "identical_nodes_coordinates_edges": True})
finally:
    globals()["TEST_DIR"] = _saved_test67
    os.environ["BIOHUB_EXP067_EXPORT"] = _saved_export67
for _stem67 in _x67_stems:
    _ev67 = _p67.load_evidence(_dir67 / f"{_stem67}.npz")
    _graph67 = _p67.load_final_graph(_dir67 / f"{_stem67}.final.npz")
    _table67 = _p67.reconcile(_graph67, _ev67)
    _labels67 = _s67.load_label_set(_dir67 / "labels" / f"{_stem67}.npz")
    assert _ev67.manifest["split"] == "train" and _labels67.stem == _stem67
    assert _ev67.manifest["weights_sha256"] == {"primary": _x67_expected_checkpoints["primary"],
        "secondary": _x67_expected_checkpoints["secondary"], "coordinate_head": _x67_head_sha}
    assert _graph67.n_nodes > 0 and _table67.reconsiderable.any()
    _rows67.append({"stem": _stem67, "nodes": _graph67.n_nodes, "edges": _graph67.n_edges,
                   "alternatives": _ev67.n_alternatives, "matched_labels": _labels67.n_matched,
                   "reconsiderable": int(_table67.reconsiderable.sum())})
_hashes67 = {str(p.relative_to(_dir67)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(_dir67.rglob("*.npz"))}
_metrics67 = {"schema_version": 1, "experiment_id": "exp_067b_temporal_feature_export_v2",
              "validation": {"protocol": "exp067_train_export_v1"},
              "primary_metric": 1.0, "gate_passed": True, "runtime_seconds": time.monotonic() - _exp067_started,
              "metric_meaning": "all explicit TRAIN exports passed identity and integrity checks; NOT accuracy",
              "per_movie": _rows67, "artifact_sha256": _hashes67,
              "python_version": platform.python_version(), "ground_truth_scope": "explicit TRAIN geff only",
              "training_executed": False, "submission_created": False,
              "representative_parent_parity": _parity67,
              "backbone_provenance": "POSSIBLE_OVERLAP_UNKNOWN_PROVENANCE",
              "coordinate_head_provenance": "same public mount; hash pinned before this run; historical exp064 head hash unavailable",
              "expected_parent_checkpoints": _x67_expected_checkpoints,
              "resolved_environment": {k: v for k, v in os.environ.items() if k.startswith(("BIOHUB_", "V1284_"))},
              "resolved_postprocess_globals": {k: v for k, v in list(globals().items()) if k.isupper() and isinstance(v, (str, int, float, bool))},
              "postprocess_base": PP_BASE_CONFIG}
Path("/kaggle/working/metrics.json").write_text(json.dumps(_metrics67, indent=2), encoding="utf-8")
print(json.dumps(_metrics67, indent=2))
'''
    nb['cells'].append({'cell_type': 'code', 'metadata': {}, 'execution_count': None,
                         'outputs': [], 'source': final})
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            compile(''.join(cell['source']), '<exp067a>', 'exec')
    path = dev / 'local_build/export_v2.ipynb'
    path.write_text(json.dumps(nb, indent=1), encoding='utf-8')
    parent = yaml.safe_load((ROOT / 'configs/exp_064_x138_verbatim_repro.yaml').read_text(encoding='utf-8'))
    kaggle = parent['kaggle']
    kaggle.pop('note', None)
    kaggle.update(slug='biohub-exp067b-temporal-export', title='biohub-exp067b-temporal-export')
    config = {
        'schema_version': 1, 'experiment_id': 'exp_067b_temporal_feature_export_v2',
        'parent': 'exp_064_x138_verbatim_repro',
        'hypothesis': 'The frozen exp064 predictor can export measured temporal features and bounded top-k alternatives ranked by logits, mapped to its unchanged final graph on explicit TRAIN movies, enabling the agreed learned joint-lineage model.',
        'change': {'component': 'measured_temporal_feature_export_v2', 'exact': 'Add export hooks and identity metadata; run eight fixed TRAIN movies. Fix controller gate and both-role eligibility; assert dependencies/config and compare disabled-hook postprocessing on one raw movie per prefix. No repeated detector inference, TEST prediction, sweep or new trained head yet.'},
        'source_notebook': path.relative_to(ROOT).as_posix(),
        'strategy_record': 'experiments/exp_067_temporal_joint_lineage/revision_acceptance_v2.md',
        'execution_authorization': 'User 2026-09-26 explicitly requested direct Kaggle trial after code completion. This first run produces data required to train the new head.',
        'validation': {'protocol': 'exp067_train_export_v1', 'primary_metric': 'binary_export_integrity',
                       'limitations': 'Engineering export gate only; no gain claim. Eight movies inherited from prior diagnostic coverage (historically label-enriched), split lexically within prefix before new-head training. Later scores are a biased local proxy, not pristine validation. Frozen backbone overlap unknown.'},
        'admission': {'require_codex_review': True, 'reviewer_provider': 'codex'},
        'local': {'smoke_test': ['{python}', 'scripts/validate_notebook.py', '{source_notebook}', '--require-metrics-contract']},
        'budget': {'tier': 1, 'expected_gpu_hours': 2.0,
                   'note': 'One attempt. Notebook watchdog kills descendant predictor processes and exits at 5400 seconds after cell0; 2h reservation includes startup margin. No automatic retries. Only export executes; pinned parent CUDA environment retained, CPU-training requirements not installed.'},
        'success': {'minimum_improvement': 0.0, 'regression_threshold': 0.0},
        'evaluation': {'mode': 'gate', 'gate_field': 'gate_passed'}, 'kaggle': kaggle,
        'revision_record': 'experiments/exp_067_temporal_joint_lineage/admission_revision_v2.md',
        'leaderboard': {'authorized': False},
        'stop_rule': 'Any identity/integrity/export failure stops the run. Do not train on incomplete exports. Collect raw failure logs; do not auto-retry. No promotion or LB submission.'}
    out = ROOT / 'configs/exp_067b_temporal_feature_export_v2.yaml'
    out.write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()

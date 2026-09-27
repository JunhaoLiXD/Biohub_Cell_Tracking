"""Freeze the exp067 Kaggle feature-export attempt (revision v3); never launch it.

v3 answers the four substantive findings of the exp067b admission review:

2. The effective predictor arguments and the *resolved* postprocessing globals are now
   asserted against the frozen exp064 parent -- computed from the parent's own source by
   scripts/exp067_parent_config.py, not retyped from notebook prose -- immediately before
   TRAIN inference starts, instead of being merely recorded after the fact. Only declared
   export differences are tolerated.
3. Observed dependency hashes and observed package versions are persisted in the final
   metrics next to the expected ones.
4. The holdout protocol is named for what it is (a within-prefix movie holdout, six train /
   two held out) and the budget is described as planned, reserved by the controller at the
   launch gate rather than claimed as already reserved.

Finding 1 (explicit consensus on the remote-trial amendment) is a record, not code: see
experiments/exp_067_temporal_joint_lineage/remote_trial_amendment_v3.md.

exp067a and exp067b keep their own snapshots, configs and reviews; nothing here rewrites them.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.exp067.patching import once, patch_notebook, patch_predictor, replay_parent  # noqa: E402
from scripts.exp067_parent_config import (  # noqa: E402
    assigned_environment_keys,
    frozen_environment,
    parent_cells,
    resolved_globals,
)

#: Revisions share this one generator on purpose: a successor must differ from its predecessor
#: only by the recorded fix, and building both from the same code is what makes that checkable.
REVISIONS = {
    'v3': {'experiment_id': 'exp_067c_temporal_feature_export_v3',
           'slug': 'biohub-exp067c-temporal-export', 'notebook': 'export_v3.ipynb',
           'config': 'configs/exp_067c_temporal_feature_export_v3.yaml', 'component_suffix': 'v3'},
    'v4': {'experiment_id': 'exp_067d_temporal_feature_export_v4',
           'slug': 'biohub-exp067d-temporal-export', 'notebook': 'export_v4.ipynb',
           'config': 'configs/exp_067d_temporal_feature_export_v4.yaml', 'component_suffix': 'v4'},
}
REVISION = REVISIONS['v4']
EXPERIMENT_ID = REVISION['experiment_id']
V1284_HEAD_SHA256 = '625a0d9340f48193f2ec294fc2d81c5bb3c03087eab78ef0ae998a9c4c7da00c'

# The export must run the held-out validator path the parent switches off, so it can reach
# TRAIN movies at all. This is the ONLY intended configuration difference from exp064.
DECLARED_ENV_DIFFERENCES = {'BIOHUB_VALIDATOR_ENABLE': ('0', '1')}
DECLARED_GLOBAL_DIFFERENCES = {'VALIDATOR_ENABLE': (False, True)}
# Additive exp067 keys; new names, never rebindings of a parent key.
DECLARED_ADDED_ENV_PREFIXES = ('BIOHUB_EXP067_',)

SPLITS = {
    'protocol': 'within_prefix_movie_holdout',
    'protocol_note': (
        'Fixed within-prefix movie holdout: six TRAIN movies fit the new head, two are held '
        'out, both prefixes present on each side. This is NOT leave-one-movie-out '
        'cross-validation and NOT a cross-domain split; the 44b6 and 6bba domains both appear '
        'in training, so it cannot establish cross-domain generalization.'),
    'train': ['44b6_12dfb391', '44b6_267148e4', '44b6_2a2eff9f',
              '6bba_062c8d37', '6bba_07e24132', '6bba_085bf656'],
    'holdout': ['44b6_341df25f', '6bba_09961292'],
    'test_stems': ['44b6_0113de3b', '44b6_0b24845f', '6bba_05b6850b', '6bba_05db0fb1'],
}

WATCHDOG = '''# Bound this first export attempt, including child predictor processes.
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


def dependency_gate(parent_receipt, literal_env, derived_env, parent_keys):
    """Checkpoint/dependency identity, plus the OBSERVED dependency receipt for metrics.

    Runs before any TRAIN inference. Environment keys the parent itself resolves at runtime
    (materialized checkpoint paths) are checked for presence and file existence; their bytes
    are already pinned by the checkpoint hashes asserted here, so asserting a literal path
    would only add a false failure mode.
    """
    expected_env = {key: value for key, value in literal_env.items()
                    if key not in DECLARED_ENV_DIFFERENCES}
    declared_env = {key: new for key, (_old, new) in DECLARED_ENV_DIFFERENCES.items()}
    # Every key the parent assigns, including ones whose value is deliberately not asserted
    # (wall clock). Narrowing this to the value-asserted keys is what failed the v1 run.
    parent_env_keys = sorted(set(parent_keys) | set(literal_env) | set(derived_env))
    return f'''# Runtime dependency/configuration gate before TRAIN inference.
import hashlib, importlib, platform
import importlib.metadata as _x67md
_x67_expected_checkpoints = {parent_receipt['checkpoint_sha256']!r}
_x67_expected_support_manifest = {parent_receipt['support_repo_python_manifest_sha256']!r}
assert _runtime_integrity_receipt["checkpoint_sha256"] == _x67_expected_checkpoints, \\
    _runtime_integrity_receipt["checkpoint_sha256"]
assert _runtime_integrity_receipt["support_repo_python_manifest_sha256"] == _x67_expected_support_manifest
assert _runtime_integrity_receipt["ground_truth_accessed"] is False
_x67_head_sha = hashlib.sha256(Path(os.environ["V1284_HEAD"]).read_bytes()).hexdigest()
assert _x67_head_sha == {V1284_HEAD_SHA256!r}, _x67_head_sha

# --- exp067 environment identity ---
# Every frozen parent assignment, with only declared differences.
_x67_expected_env = {expected_env!r}
_x67_declared_env = {declared_env!r}
_x67_runtime_env_keys = {sorted(derived_env)!r}
_x67_parent_env_keys = {parent_env_keys!r}
_x67_env_mismatch = {{k: (v, os.environ.get(k)) for k, v in _x67_expected_env.items()
                     if os.environ.get(k) != v}}
_x67_env_mismatch.update({{k: ("DECLARED " + v, os.environ.get(k))
                          for k, v in _x67_declared_env.items() if os.environ.get(k) != v}})
assert not _x67_env_mismatch, _x67_env_mismatch
_x67_runtime_env = {{}}
for _k67 in _x67_runtime_env_keys:
    _v67 = os.environ.get(_k67)
    assert _v67 and Path(_v67).is_file(), (_k67, _v67)
    _x67_runtime_env[_k67] = _v67
# Nothing configures this pipeline that the frozen parent did not, apart from additive
# exp067 keys under their own prefix.
_x67_unexpected_env = sorted(k for k in os.environ
    if (k.startswith("BIOHUB_") or k.startswith("V1284_"))
    and k not in _x67_parent_env_keys and not k.startswith({DECLARED_ADDED_ENV_PREFIXES!r}))
assert not _x67_unexpected_env, _x67_unexpected_env

# --- exp067 observed dependency receipt ---
# What actually loaded, recorded beside what was expected.
_x67_observed_packages = {{}}
for _name67, (_module67, _spec67) in PACKAGE_SPECS.items():
    _dist67 = _spec67.split(">=")[0].split("<")[0].split("==")[0].strip()
    try:
        _x67_observed_packages[_dist67] = _x67md.version(_dist67)
    except Exception:
        try:
            _x67_observed_packages[_dist67] = getattr(
                importlib.import_module(_module67), "__version__", "unknown")
        except Exception as _exc67:
            _x67_observed_packages[_dist67] = "unavailable: " + type(_exc67).__name__
for _dist67 in ("torch", "numpy", "scipy"):
    try:
        _x67_observed_packages[_dist67] = _x67md.version(_dist67)
    except Exception:
        _x67_observed_packages[_dist67] = "unavailable"
_x67_observed_dependencies = {{
    "checkpoint_sha256": dict(_runtime_integrity_receipt["checkpoint_sha256"]),
    "support_repo_python_manifest_sha256":
        _runtime_integrity_receipt["support_repo_python_manifest_sha256"],
    "support_repo_python_file_count":
        _runtime_integrity_receipt["support_repo_python_file_count"],
    "materialized_paths": dict(_runtime_integrity_receipt["materialized_paths"]),
    "coordinate_head_sha256": _x67_head_sha,
    "runtime_resolved_environment": _x67_runtime_env,
    "package_versions": _x67_observed_packages,
    "python_version": platform.python_version(),
    "platform": platform.platform(),
    "torch_version": _torch.__version__,
    "torch_cuda": getattr(_torch.version, "cuda", None),
    "gpu_names": [_torch.cuda.get_device_name(_i67) for _i67 in range(_torch.cuda.device_count())],
}}
print("exp067 dependency gate passed;", len(_x67_observed_packages), "package versions observed")
'''


def effective_configuration_gate(expected, unresolved):
    """Assert the RESOLVED parent configuration and the effective predictor argv.

    Injected inside the validator cell after every configuration global has been bound and
    after ``predict_val_cmd`` is fully assembled, but before the predictor subprocess starts.
    """
    declared = {name: new for name, (_old, new) in DECLARED_GLOBAL_DIFFERENCES.items()}
    asserted = {name: value for name, value in expected.items() if name not in declared}
    # Keep the reason readable in the notebook and in metrics; the full source stays in the
    # frozen parent snapshot, which is where an auditor would look for it anyway.
    unresolved = {name: (reason[:157] + '...' if len(reason) > 160 else reason)
                  for name, reason in unresolved.items()}
    return f'''    # --- exp067 resolved globals ---
    # Effective-configuration gate: resolved parent state, asserted before inference.
    # Expected values were derived from the frozen exp064 notebook source and its frozen
    # environment by scripts/exp067_parent_config.py, not retyped from notebook prose.
    _x67_expected_globals = {asserted!r}
    _x67_declared_globals = {declared!r}
    # Deliberately not asserted: Kaggle-mount paths, containers, loaded model bundles and
    # wall clock, which are runtime discoveries rather than frozen configuration.
    _x67_unasserted_globals = {unresolved!r}
    _x67_global_mismatch = {{}}
    for _k67 in list(_x67_expected_globals) + list(_x67_declared_globals):
        _e67 = _x67_declared_globals[_k67] if _k67 in _x67_declared_globals else _x67_expected_globals[_k67]
        if _k67 not in globals():
            _x67_global_mismatch[_k67] = (_e67, "MISSING")
            continue
        _a67 = globals()[_k67]
        if type(_a67) is not type(_e67) or _a67 != _e67:
            _x67_global_mismatch[_k67] = (_e67, _a67)
    assert not _x67_global_mismatch, _x67_global_mismatch

    # --- exp067 effective predictor arguments ---
    # Rebuilt from the frozen expectation rather than from the live globals, so a drifted
    # global cannot validate itself.
    assert TRAIN_DIR == COMP_DIR / "train" and TRAIN_DIR.is_dir(), TRAIN_DIR
    assert val_splits_path.name == "kaggle_val_splits.json", val_splits_path
    _x67_expected_argv = [
        sys.executable, "scripts/predict_unet_transformer.py",
        "--data-dir", str(TRAIN_DIR),
        "--splits", "kaggle_val_splits.json",
        "--split", "0",
        "--weights", _x67_expected_globals["WEIGHTS_RELATIVE"],
        "--unet-batch-size", str(_x67_expected_globals["UNET_BATCH_SIZE"]),
        "--det-threshold", str(_x67_expected_globals["DET_THRESHOLD"]),
        "--ilp-edge-weight", str(_x67_expected_globals["ILP_EDGE_WEIGHT"]),
        "--ilp-appearance-weight", str(_x67_expected_globals["ILP_APPEARANCE_WEIGHT"]),
        "--ilp-disappearance-weight", str(_x67_expected_globals["ILP_DISAPPEARANCE_WEIGHT"]),
        "--ilp-division-weight", str(_x67_expected_globals["ILP_DIVISION_WEIGHT"]),
    ]
    if _x67_expected_globals["USE_ILP"]:
        _x67_expected_argv.append("--use-ilp")
    assert predict_val_cmd == _x67_expected_argv, {{
        "expected": _x67_expected_argv, "actual": predict_val_cmd}}
    # The subprocess environment differs from the parent's only by the prepended exp067
    # runtime root on PYTHONPATH; the parent's own "src" suffix is preserved below.
    assert os.environ["PYTHONPATH"].startswith(str(_x67root)), os.environ["PYTHONPATH"]
    _x67_effective_configuration = {{
        "predictor_argv": list(predict_val_cmd),
        "asserted_globals": len(_x67_expected_globals),
        "declared_global_differences": {DECLARED_GLOBAL_DIFFERENCES!r},
        "declared_environment_differences": {DECLARED_ENV_DIFFERENCES!r},
        "unasserted_globals": _x67_unasserted_globals,
    }}
    print("exp067 effective-configuration gate passed;", len(_x67_expected_globals),
          "globals and", len(predict_val_cmd), "predictor arguments")
'''


FINAL_GATE = '''# Structured engineering gate: exported artifacts, not an accuracy claim.
import hashlib, json, platform, copy
from scripts.exp067 import provenance as _p67, supervise as _s67
_x67rt.raise_if_fatal()
assert _x67_effective_configuration["asserted_globals"] > 0, "effective-configuration gate did not run"
_rows67 = []
_dir67 = Path(os.environ["BIOHUB_EXP067_EXPORT_DIR"])
_parity67 = []
# Representative control: same raw graphs, hooks disabled; no repeated detector inference.
# This tests postprocessing preservation only -- NOT detector or association equivalence.
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
# PP_BASE_CONFIG is built from globals the effective-configuration gate already asserted;
# re-checking it here proves the sweep key list itself was not redefined.
assert PP_BASE_CONFIG == {k: _x67_expected_globals[k] for k in PP_SWEEP_KEYS}, PP_BASE_CONFIG
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
_metrics67 = {"schema_version": 1, "experiment_id": "EXPERIMENT_ID_PLACEHOLDER",
              "validation": {"protocol": "exp067_train_export_v1",
                             "split_protocol": "within_prefix_movie_holdout",
                             "split_protocol_note": "SPLIT_NOTE_PLACEHOLDER"},
              "primary_metric": 1.0, "gate_passed": True, "runtime_seconds": time.monotonic() - _exp067_started,
              "metric_meaning": "all explicit TRAIN exports passed identity and integrity checks; NOT accuracy",
              "per_movie": _rows67, "artifact_sha256": _hashes67,
              "python_version": platform.python_version(), "ground_truth_scope": "explicit TRAIN geff only",
              "training_executed": False, "submission_created": False,
              "representative_parent_parity": _parity67,
              "representative_parent_parity_scope":
                  "one movie per prefix; reuses the instrumented raw graphs, so it evidences "
                  "postprocessing preservation only, not detector or association equivalence",
              "backbone_provenance": "POSSIBLE_OVERLAP_UNKNOWN_PROVENANCE",
              "coordinate_head_provenance": "same public mount; hash pinned before this run; historical exp064 head hash unavailable",
              "expected_parent_checkpoints": _x67_expected_checkpoints,
              "expected_support_repo_python_manifest_sha256": _x67_expected_support_manifest,
              "observed_dependencies": _x67_observed_dependencies,
              "effective_configuration": _x67_effective_configuration,
              "resolved_environment": {k: v for k, v in os.environ.items() if k.startswith(("BIOHUB_", "V1284_"))},
              "resolved_postprocess_globals": {k: v for k, v in list(globals().items()) if k.isupper() and isinstance(v, (str, int, float, bool))},
              "postprocess_base": PP_BASE_CONFIG}
Path("/kaggle/working/metrics.json").write_text(json.dumps(_metrics67, indent=2), encoding="utf-8")
print(json.dumps(_metrics67, indent=2))
'''


def build_notebook():
    """Return (notebook, build summary) for the frozen v3 export attempt."""
    cells = parent_cells()
    literal_env, derived_env = frozen_environment(cells)
    expected_globals, unresolved_globals = resolved_globals(cells, literal_env)
    for name, (old, _new) in DECLARED_GLOBAL_DIFFERENCES.items():
        if expected_globals.get(name) != old:
            raise ValueError(f'declared global difference does not match the parent: {name}')
    for key, (old, _new) in DECLARED_ENV_DIFFERENCES.items():
        if literal_env.get(key) != old:
            raise ValueError(f'declared environment difference does not match the parent: {key}')

    compile(patch_predictor(replay_parent()), '<actual patched predictor>', 'exec')
    nb = patch_notebook('export', SPLITS['train'] + SPLITS['holdout'])

    # The validator path is the only route to TRAIN movies; make its use explicit instead of
    # implicit in an `if`, so the configuration gate below can never be silently skipped.
    validator = next(index for index, cell in enumerate(nb['cells'])
                     if '_val_start = time.time()' in ''.join(cell['source']))
    source = ''.join(nb['cells'][validator]['source'])
    source = once(source, 'os.environ["BIOHUB_EXP067_SPLIT"] = "train"\n',
                  'os.environ["BIOHUB_EXP067_SPLIT"] = "train"\n'
                  'assert VALIDATOR_ENABLE is True and val_stems, '
                  '"exp067 export requires the validator path"\n')
    source = once(source, '    _val_start = time.time()\n',
                  effective_configuration_gate(expected_globals, unresolved_globals)
                  + '    _val_start = time.time()\n')
    nb['cells'][validator]['source'] = source

    nb['cells'].insert(1, {'cell_type': 'code', 'metadata': {}, 'execution_count': None,
                           'outputs': [], 'source': WATCHDOG})
    parent_receipt = json.loads((ROOT / 'experiments/exp_064_x138_verbatim_repro/collection'
                                 '/bidirectional_production_runtime_integrity.json')
                                .read_text(encoding='utf-8'))
    # Original cell4 is index 6 after the two bootstrap cells; inference is skipped there.
    nb['cells'].insert(7, {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [],
                           'source': dependency_gate(parent_receipt, literal_env, derived_env,
                                                     assigned_environment_keys(cells))})
    final = (FINAL_GATE.replace('EXPERIMENT_ID_PLACEHOLDER', EXPERIMENT_ID)
             .replace('SPLIT_NOTE_PLACEHOLDER', SPLITS['protocol_note']))
    nb['cells'].append({'cell_type': 'code', 'metadata': {}, 'execution_count': None,
                        'outputs': [], 'source': final})
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            compile(''.join(cell['source']), '<exp067c>', 'exec')
    summary = {
        'cells': len(nb['cells']),
        'asserted_globals': len(expected_globals) - len(DECLARED_GLOBAL_DIFFERENCES),
        'declared_global_differences': DECLARED_GLOBAL_DIFFERENCES,
        'unasserted_globals': sorted(unresolved_globals),
        'asserted_env_keys': len(literal_env) - len(DECLARED_ENV_DIFFERENCES),
        'declared_env_differences': DECLARED_ENV_DIFFERENCES,
        'runtime_resolved_env_keys': sorted(derived_env),
    }
    return nb, summary


def main():
    dev = ROOT / 'experiments/exp_067_temporal_joint_lineage'
    (dev / 'splits_v2.json').write_text(json.dumps(SPLITS, indent=2), encoding='utf-8')
    nb, summary = build_notebook()
    path = dev / 'local_build' / REVISION['notebook']
    path.write_text(json.dumps(nb, indent=1), encoding='utf-8')

    parent = yaml.safe_load((ROOT / 'configs/exp_064_x138_verbatim_repro.yaml')
                            .read_text(encoding='utf-8'))
    kaggle = parent['kaggle']
    kaggle.pop('note', None)
    kaggle.update(slug=REVISION['slug'], title=REVISION['slug'])
    config = {
        'schema_version': 1, 'experiment_id': EXPERIMENT_ID,
        'parent': 'exp_064_x138_verbatim_repro',
        'hypothesis': (
            'The frozen exp064 predictor can export measured temporal features and bounded '
            'top-k alternatives ranked by logits, mapped to its unchanged final graph on '
            'explicit TRAIN movies, enabling the agreed learned joint-lineage model.'),
        'change': {
            'component': 'measured_temporal_feature_export_' + REVISION['component_suffix'],
            'exact': (
                'Add export hooks and identity metadata; run eight fixed TRAIN movies. Assert '
                'the resolved parent globals and the effective predictor argv against the '
                'frozen exp064 configuration before inference, allowing only the declared '
                'validator-enable difference; persist observed dependency hashes and package '
                'versions in metrics. No repeated detector inference, TEST prediction, sweep '
                'or trained head yet. v4 fixes the exp067c v1 gate defect: the stray-key '
                "allow-list is built from EVERY environment key the parent assigns, not from the "
                'value-asserted subset, so the wall-clock key the parent legitimately sets is no '
                'longer rejected as unexpected. No other change.')},
        'source_notebook': path.relative_to(ROOT).as_posix(),
        'strategy_record':
            'experiments/exp_067_temporal_joint_lineage/remote_trial_amendment_v3.md',
        'execution_authorization': (
            'User 2026-09-26 explicitly requested a direct Kaggle trial after code completion. '
            'This first run produces the data required to train the new head. The launch still '
            'goes through the controller gates: fresh admission review, snapshot smoke and an '
            'explicit budget reservation.'),
        'validation': {
            'protocol': 'exp067_train_export_v1',
            'primary_metric': 'binary_export_integrity',
            'split_protocol': SPLITS['protocol'],
            'split_protocol_note': SPLITS['protocol_note'],
            'limitations': (
                'Engineering export gate only; no gain claim. Eight movies inherited from prior '
                'diagnostic coverage (historically label-enriched), split within prefix before '
                'new-head training. Later scores from this split are a biased local proxy, not '
                'pristine validation, and cannot show cross-domain generalization. Frozen '
                'backbone overlap unknown. Representative parent parity reuses the instrumented '
                'raw graphs, so it evidences postprocessing preservation only, not detector or '
                'association equivalence.')},
        'admission': {'require_codex_review': True, 'reviewer_provider': 'codex'},
        'local': {'smoke_test': ['{python}', 'scripts/validate_notebook.py', '{source_notebook}',
                                 '--require-metrics-contract']},
        'budget': {
            'tier': 1, 'expected_gpu_hours': 2.0,
            'note': (
                'One attempt. PLANNED allocation of 2.0 GPU hours; the controller reserves it at '
                'the launch gate and this config does not claim it is already reserved. The '
                'notebook watchdog kills descendant predictor processes and exits 5400 seconds '
                'after cell0; the 2 h figure includes startup margin. No automatic retries. Only '
                'the export executes; the pinned parent CUDA image is retained and the separate '
                'CPU training requirements are not installed into it.')},
        'success': {'minimum_improvement': 0.0, 'regression_threshold': 0.0},
        'evaluation': {'mode': 'gate', 'gate_field': 'gate_passed'}, 'kaggle': kaggle,
        'revision_record':
            'experiments/exp_067_temporal_joint_lineage/remote_trial_amendment_v3.md',
        'leaderboard': {'authorized': False},
        'stop_rule': (
            'Any identity, configuration, integrity or export failure stops the run. Do not train '
            'on incomplete exports. Collect raw failure logs; do not auto-retry. No promotion or '
            'LB submission.')}
    out = ROOT / REVISION['config']
    out.write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
    summary['notebook'] = path.relative_to(ROOT).as_posix()
    summary['config'] = out.relative_to(ROOT).as_posix()
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()

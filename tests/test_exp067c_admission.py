"""Behavioral checks for the exp067c (v3) frozen export attempt.

These cover the three code-level findings of the exp067b admission review: the effective
configuration must be asserted against the frozen exp064 parent *before* inference rather
than recorded after it, and the observed dependency receipt must reach the metrics contract.
The gates are executed here, not merely pattern-matched, so a gate that would accept drift
fails the suite.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import prepare_exp067_export_v3 as V3  # noqa: E402
from scripts.exp067_parent_config import (  # noqa: E402
    assigned_environment_keys,
    frozen_environment,
    parent_cells,
    resolved_globals,
)

# Follows whichever revision the generator is currently set to build.
NOTEBOOK = (ROOT / 'experiments/exp_067_temporal_joint_lineage/local_build'
            / V3.REVISION['notebook'])


@pytest.fixture(scope='module')
def built():
    notebook, summary = V3.build_notebook()
    sources = [''.join(cell['source']) for cell in notebook['cells']]
    dependency = next(s for s in sources if '--- exp067 environment identity ---' in s)
    validator = next(s for s in sources if '--- exp067 resolved globals ---' in s)
    return SimpleNamespace(notebook=notebook, summary=summary, sources=sources,
                           dependency=dependency, validator=validator)


@pytest.fixture(scope='module')
def parent():
    cells = parent_cells()
    literal_env, derived_env = frozen_environment(cells)
    globals_, unresolved = resolved_globals(cells, literal_env)
    return SimpleNamespace(literal_env=literal_env, derived_env=derived_env,
                           globals=globals_, unresolved=unresolved)


def slice_between(source: str, start: str, end: str | None) -> str:
    """Cut a gate section out of a generated cell, keeping whole lines so dedent works."""
    begin = source.rindex('\n', 0, source.index(start)) + 1
    stop = source.rindex('\n', 0, source.index(end)) + 1 if end else len(source)
    return textwrap.dedent(source[begin:stop])


def run(source: str, namespace: dict) -> dict:
    exec(compile(source, '<gate>', 'exec'), namespace)
    return namespace


def test_frozen_notebook_matches_the_builder(built):
    """The snapshot on disk is what the builder produces; nothing was hand-edited into it."""
    assert json.loads(NOTEBOOK.read_text(encoding='utf-8')) == built.notebook


def test_declared_differences_are_the_only_intended_drift(parent):
    for key, (old, new) in V3.DECLARED_ENV_DIFFERENCES.items():
        assert parent.literal_env[key] == old and old != new
    for name, (old, new) in V3.DECLARED_GLOBAL_DIFFERENCES.items():
        assert parent.globals[name] == old and old != new


def test_configuration_gates_run_before_any_inference(built):
    """A gate that runs after the predictor has already started proves nothing."""
    dependency_index = built.sources.index(built.dependency)
    validator_index = built.sources.index(built.validator)
    inference = next(i for i, s in enumerate(built.sources) if 'subprocess.Popen(' in s)
    assert dependency_index < validator_index <= inference
    gate = built.validator.index('--- exp067 resolved globals ---')
    for launch in ('subprocess.Popen(', 'subprocess.run('):
        assert gate < built.validator.index(launch)
    # The predictor argv is asserted only once the full command, ILP flag included, exists.
    assert built.validator.index('predict_val_cmd.append("--use-ilp")') < gate


def test_resolved_globals_gate_rejects_drift(built, parent):
    body = slice_between(built.validator, '# --- exp067 resolved globals ---',
                         '# --- exp067 effective predictor arguments ---')
    expected = {name: value for name, value in parent.globals.items()
                if name not in V3.DECLARED_GLOBAL_DIFFERENCES}
    declared = {name: new for name, (_old, new) in V3.DECLARED_GLOBAL_DIFFERENCES.items()}

    run(body, {**expected, **declared})  # the frozen parent configuration passes

    drifted = dict(expected)
    drifted['SAFE_DIV_MAX_UM'] = expected['SAFE_DIV_MAX_UM'] + 0.5
    with pytest.raises(AssertionError, match='SAFE_DIV_MAX_UM'):
        run(body, {**drifted, **declared})

    # A bool silently standing in for the int it equals is still drift.
    retyped = dict(expected)
    retyped['OUTPUT_MIN_TRACK_LEN'] = True
    with pytest.raises(AssertionError, match='OUTPUT_MIN_TRACK_LEN'):
        run(body, {**retyped, **declared})

    missing = {k: v for k, v in expected.items() if k != 'DET_THRESHOLD'}
    with pytest.raises(AssertionError, match='DET_THRESHOLD'):
        run(body, {**missing, **declared})

    # The declared export difference must still be checked, not merely exempted.
    with pytest.raises(AssertionError, match='VALIDATOR_ENABLE'):
        run(body, {**expected, 'VALIDATOR_ENABLE': False})


def test_stray_key_allowlist_covers_every_key_the_parent_assigns(built, parent):
    """Regression for the exp067c v1 failure.

    A key whose VALUE we decline to assert -- wall clock -- is still a key the parent legitimately
    sets. v1 conflated the two sets, so its own stray-key check rejected
    ``BIOHUB_KERNEL_START_TS`` after 464 s of real GPU time. The allow-list must therefore be a
    superset of every environment key the parent notebook assigns.
    """
    body = slice_between(built.dependency, '# --- exp067 environment identity ---',
                         '# --- exp067 observed dependency receipt ---')
    namespace = {'os': SimpleNamespace(environ={}), 'Path': Path}
    exec(compile(body.split('_x67_env_mismatch =')[0], '<allowlist>', 'exec'), namespace)
    allowed = set(namespace['_x67_parent_env_keys'])
    assigned = assigned_environment_keys(parent_cells())
    assert not assigned - allowed, sorted(assigned - allowed)
    assert 'BIOHUB_KERNEL_START_TS' in allowed
    # ...but its value is still not asserted, because it is wall clock.
    assert 'BIOHUB_KERNEL_START_TS' not in namespace['_x67_expected_env']


def test_environment_gate_accepts_the_real_parent_key_set(built, parent, tmp_path):
    """The gate must pass on an environment that contains every key the parent actually sets."""
    body = slice_between(built.dependency, '# --- exp067 environment identity ---',
                         '# --- exp067 observed dependency receipt ---')
    checkpoint = tmp_path / 'weights.pt'
    checkpoint.write_bytes(b'0')
    environ = dict(parent.literal_env)
    for key, (_old, new) in V3.DECLARED_ENV_DIFFERENCES.items():
        environ[key] = new
    for key in parent.derived_env:
        environ[key] = str(checkpoint)
    for key in assigned_environment_keys(parent_cells()):
        environ.setdefault(key, '1758900000.0')  # wall clock and anything else the parent assigns
    environ['BIOHUB_EXP067_EXPORT'] = '1'
    run(body, {'os': SimpleNamespace(environ=environ), 'Path': Path})


def test_environment_gate_rejects_drift_and_stray_keys(built, parent, tmp_path):
    body = slice_between(built.dependency, '# --- exp067 environment identity ---',
                         '# --- exp067 observed dependency receipt ---')
    checkpoint = tmp_path / 'weights.pt'
    checkpoint.write_bytes(b'0')
    environ = dict(parent.literal_env)
    for key, (_old, new) in V3.DECLARED_ENV_DIFFERENCES.items():
        environ[key] = new
    for key in parent.derived_env:
        environ[key] = str(checkpoint)
    environ['BIOHUB_EXP067_EXPORT'] = '1'  # additive exp067 key, allowed by declaration

    namespace = {'os': SimpleNamespace(environ=dict(environ)), 'Path': Path}
    result = run(body, namespace)
    assert result['_x67_runtime_env'] == {k: str(checkpoint) for k in parent.derived_env}

    drifted = dict(environ)
    drifted['BIOHUB_DET_THRESHOLD'] = '0.9'
    with pytest.raises(AssertionError, match='BIOHUB_DET_THRESHOLD'):
        run(body, {'os': SimpleNamespace(environ=drifted), 'Path': Path})

    reverted = dict(environ)
    reverted['BIOHUB_VALIDATOR_ENABLE'] = '0'
    with pytest.raises(AssertionError, match='BIOHUB_VALIDATOR_ENABLE'):
        run(body, {'os': SimpleNamespace(environ=reverted), 'Path': Path})

    stray = dict(environ)
    stray['BIOHUB_SOME_NEW_KNOB'] = '1'
    with pytest.raises(AssertionError, match='BIOHUB_SOME_NEW_KNOB'):
        run(body, {'os': SimpleNamespace(environ=stray), 'Path': Path})

    absent = dict(environ)
    absent[next(iter(parent.derived_env))] = str(tmp_path / 'nope.pt')
    with pytest.raises(AssertionError):
        run(body, {'os': SimpleNamespace(environ=absent), 'Path': Path})


def test_predictor_argv_gate_rejects_drift(built, parent, tmp_path):
    body = slice_between(built.validator, '# --- exp067 effective predictor arguments ---',
                         '_val_start = time.time()')
    expected = {name: value for name, value in parent.globals.items()
                if name not in V3.DECLARED_GLOBAL_DIFFERENCES}
    competition = tmp_path / 'comp'
    (competition / 'train').mkdir(parents=True)
    runtime_root = tmp_path / 'exp067_runtime'

    def namespace(argv):
        return {
            'sys': sys, 'os': SimpleNamespace(environ={'PYTHONPATH': f'{runtime_root}:src'}),
            'TRAIN_DIR': competition / 'train', 'COMP_DIR': competition,
            'val_splits_path': Path('/repo/kaggle_val_splits.json'),
            'predict_val_cmd': argv, '_x67_expected_globals': expected,
            '_x67_unasserted_globals': {}, '_x67root': runtime_root,
        }

    parent_argv = [
        sys.executable, 'scripts/predict_unet_transformer.py',
        '--data-dir', str(competition / 'train'),
        '--splits', 'kaggle_val_splits.json', '--split', '0',
        '--weights', expected['WEIGHTS_RELATIVE'],
        '--unet-batch-size', str(expected['UNET_BATCH_SIZE']),
        '--det-threshold', str(expected['DET_THRESHOLD']),
        '--ilp-edge-weight', str(expected['ILP_EDGE_WEIGHT']),
        '--ilp-appearance-weight', str(expected['ILP_APPEARANCE_WEIGHT']),
        '--ilp-disappearance-weight', str(expected['ILP_DISAPPEARANCE_WEIGHT']),
        '--ilp-division-weight', str(expected['ILP_DIVISION_WEIGHT']), '--use-ilp',
    ]
    result = run(body, namespace(list(parent_argv)))
    assert result['_x67_effective_configuration']['predictor_argv'] == parent_argv

    for index, replacement in ((parent_argv.index('--det-threshold') + 1, '0.9'),
                               (parent_argv.index('--weights') + 1, 'weights/other.pth')):
        drifted = list(parent_argv)
        drifted[index] = replacement
        with pytest.raises(AssertionError):
            run(body, namespace(drifted))

    with pytest.raises(AssertionError):
        run(body, namespace([a for a in parent_argv if a != '--use-ilp']))

    # The exp067 runtime bundle must be on PYTHONPATH, or the export hooks never import.
    stripped = namespace(list(parent_argv))
    stripped['os'] = SimpleNamespace(environ={'PYTHONPATH': 'src'})
    with pytest.raises(AssertionError):
        run(body, stripped)


def test_metrics_contract_carries_observed_provenance_and_the_real_split_name(built):
    final = built.sources[-1]
    for field in ('observed_dependencies', 'effective_configuration',
                  'expected_parent_checkpoints', 'representative_parent_parity_scope',
                  'within_prefix_movie_holdout'):
        assert field in final
    assert 'metrics.json' in final
    # The gate must be unable to pass while the effective-configuration gate was skipped.
    assert '_x67_effective_configuration["asserted_globals"]' in final
    # The run must not describe its own split as a cross-validation loop it never runs.
    assert '"split_protocol": "within_prefix_movie_holdout"' in final
    assert 'leave_one_movie_out' not in final


def test_split_record_and_config_name_the_protocol_honestly():
    splits = json.loads((ROOT / 'experiments/exp_067_temporal_joint_lineage/splits_v2.json')
                        .read_text(encoding='utf-8'))
    assert splits['protocol'] == 'within_prefix_movie_holdout'
    assert len(splits['train']) == 6 and len(splits['holdout']) == 2
    assert not set(splits['train']) & set(splits['holdout'])
    assert not (set(splits['train']) | set(splits['holdout'])) & set(splits['test_stems'])
    assert 'NOT leave-one-movie-out' in splits['protocol_note']

    import yaml
    config = yaml.safe_load((ROOT / V3.REVISION['config']).read_text(encoding='utf-8'))
    assert config['validation']['split_protocol'] == 'within_prefix_movie_holdout'
    assert config['leaderboard']['authorized'] is False
    assert config['admission']['require_codex_review'] is True
    # Budget wording: planned, not claimed as reserved.
    assert 'PLANNED' in config['budget']['note'] and 'reserved' not in config['budget']['note'].split('PLANNED')[0]

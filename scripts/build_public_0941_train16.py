"""Adapt the frozen 0.941 inference to the frozen train16 selection and scorer."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / 'experiments/repro_038_public_0941_exact_copy/snapshot/source/public_0941_exact_copy.ipynb'
ANCHOR = ROOT / 'experiments/val_008_public_0933_train16_launchable/snapshot/source/repro_public_0933.ipynb'
TARGET = ROOT / '.private/current/public_0941_train16.ipynb'
PARENT_SHA = '24253cae5a958b83d69e201719388031f5758080c5d01ca1a8e374f3a8225389'
SUBMISSION_SHA = 'bf66c879298e71c5cce0326fbac5956ca567a344ae28f0d402dfc5003fba52bd'


def source(cell):
    return ''.join(cell['source'])


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f'Expected exactly one replacement for {old[:90]!r}')
    return text.replace(old, new, 1)


def cell(text, kind='code'):
    result = {'cell_type': kind, 'metadata': {}, 'source': text.splitlines(keepends=True)}
    if kind == 'code':
        result.update(outputs=[], execution_count=None)
    return result


def build():
    if hashlib.sha256(PARENT.read_bytes()).hexdigest() != PARENT_SHA:
        raise ValueError('Frozen public parent changed')
    notebook = json.loads(PARENT.read_text(encoding='utf-8'))
    original = copy.deepcopy(notebook['cells'])
    anchor = json.loads(ANCHOR.read_text(encoding='utf-8'))
    metrics = json.loads((ANCHOR.parents[2] / 'metrics.json').read_text(encoding='utf-8'))
    expected = {s: metrics['specimen_metrics'][s]['samples'] for s in ('44b6', '6bba')}
    positives = {s: metrics['specimen_metrics'][s]['division_positive_samples'] for s in expected}
    # Only add telemetry to the successful loader return; model operations are unchanged.
    loader = replace_once(source(original[5]), '                "path": checkpoint_path,',
                          '                "path": checkpoint_path,\n'
                          '                "checkpoint_epoch": checkpoint_epoch,\n'
                          '                "checkpoint_sha256": _sha256_file(checkpoint_path),')
    notebook['cells'][5] = cell(loader)
    audit = source(original[6])
    begin = audit.index('    "configuration": {')
    end = audit.index('    "hardware": {', begin)
    audit = audit[:begin] + '''    "configuration": {
        **CONFIG_DISPLAY,
        "secondary_detection_weight": float(os.environ["BIOHUB_SECONDARY_DETECTION_WEIGHT"]),
        "secondary_edge_weight": float(os.environ["BIOHUB_SECONDARY_EDGE_WEIGHT"]),
        "bidirectional_primary_weight": float(os.environ["BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT"]),
        "secondary_link_mode": os.environ["BIOHUB_SECONDARY_LINK_MODE"],
        "secondary_low_margin_max": float(os.environ["BIOHUB_SECONDARY_LOW_MARGIN_MAX"]),
        "edge_candidate_threshold": float(os.environ["BIOHUB_DUAL_SEED_EDGE_THRESHOLD"]),
        "minimum_candidate_retention": float(os.environ["BIOHUB_DUAL_SEED_MIN_CANDIDATE_RETENTION"]),
        "fallback_scope": "individual_frame",
    },
''' + audit[end:]
    for old, new in {
        '"experiment": "harmonic_bidirectional_association_v1"': '"experiment": "val_039_public_0941_train16"',
        '"parent_experiment": "paired_bidirectional_primary_weight020_vs_forward_v1"': '"parent_experiment": "repro_038_public_0941_exact_copy"',
        '"source_kernel": "raykkretzschmar/biohub-bidirectional-primary-union13-diagnostic-v1"': '"source_kernel": "analyticaobscura/biohub-lb-941"',
        '"source_notebook_sha256": "3e65ca691941949196bf417030ea84fccafe16baaec174b2a63540451bb937e8"': f'"source_notebook_sha256": "{PARENT_SHA}"',
    }.items():
        audit = replace_once(audit, old, new)
    notebook['cells'][6] = cell(audit)
    # Reuse the exact established selector and its inference runner.
    selection = source(anchor['cells'][18])
    checks = '''
if val_stems != [stem for specimen in ("44b6", "6bba") for stem in FROZEN_SAMPLES[specimen]]:
    raise RuntimeError("Frozen train16 sample identity/order changed")
for specimen, stems in FROZEN_POSITIVES.items():
    if set(stems) != {s for s in FROZEN_SAMPLES[specimen] if division_flags[s]}:
        raise RuntimeError("Frozen division strata changed")
if not (VALIDATOR_ENABLE and VALIDATOR_N_PER_TYPE == 8
        and VALIDATOR_DIVISION_TARGET_PER_TYPE == 4
        and VALIDATOR_MATCH_RADIUS_UM == 7.0
        and VALIDATOR_NODE_COUNT_PENALTY_A == 0.1
        and VALIDATOR_DIVISION_WEIGHT == 0.1):
    raise RuntimeError("Frozen validator configuration changed")
'''
    selection = replace_once(selection, '\npredict_val_seconds = None', checks + '\npredict_val_seconds = None')
    notebook['cells'][7] = cell(selection)
    scorer = source(anchor['cells'][20])
    scorer = replace_once(scorer, '        pred_nodes_plain = nodes_by_id_to_plain(processed_nodes)',
                          '        VALIDATION_STAGE_STATS[stem] = _stage_stats\n'
                          '        pred_nodes_plain = nodes_by_id_to_plain(processed_nodes)')
    notebook['cells'][8] = cell(scorer)
    preflight = (ROOT / 'scripts/public_0941_train16_preflight.py').read_text(encoding='utf-8')
    contract = (ROOT / 'scripts/public_0941_train16_contract.py').read_text(encoding='utf-8')
    constants = (f'FROZEN_SAMPLES = {expected!r}\nFROZEN_POSITIVES = {positives!r}\n'
                 f'EXPECTED_SUBMISSION_SHA = {SUBMISSION_SHA!r}\nVALIDATION_STAGE_STATS = {{}}\n')
    notebook['cells'].insert(7, cell(constants + preflight))
    notebook['cells'].insert(0, cell('import time as _run_time\nRUN_STARTED_AT = _run_time.perf_counter()\n'))
    notebook['cells'].insert(0, cell(
        '# Public 0.941: frozen train16 validation baseline\n\n'
        'Adapted from analyticaobscura/biohub-lb-941, frozen in repro_038. '
        'Kaggle submission 56044403 completed at Public LB 0.941. '
        'Released pretrained weights are used without training. Inference is retained; '
        'only loader telemetry, reporting, and validation instrumentation are adapted. '
        'The fixed val_008 selector and scorer provide an optimistic training-derived proxy. '
        'Test submission bytes must equal repro_038 before and after validation. '
        'This establishes a baseline and does not attribute gains to individual mechanisms.\n', 'markdown'))
    notebook['cells'].append(cell(contract))
    for c in notebook['cells']:
        if c['cell_type'] == 'code':
            c['outputs'], c['execution_count'] = [], None
            ast.parse(source(c))
    return notebook


if __name__ == '__main__':
    TARGET.write_text(json.dumps(build(), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(TARGET)

"""Verify the adapter preserves inference and refuses incomplete or corrupt zon output."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from build_exp061_lb_repair import (
    BASE, REFERENCE, FINAL, IDENTITY_LINE, WATCHDOG_NEW, WATCHDOG_OLD,
    METRIC_PROSE_NEW, METRIC_PROSE_OLD, PROTOCOL_NEW, PROTOCOL_OLD,
)

def validate(path):
    base = json.loads(BASE.read_text(encoding='utf-8'))
    nb = json.loads(Path(path).read_text(encoding='utf-8'))
    assert len(nb['cells']) == len(base['cells'])
    for i in range(2):
        assert nb['cells'][i]['source'] == base['cells'][i]['source']
    assert ''.join(nb['cells'][2]['source']).replace(IDENTITY_LINE, '').replace(WATCHDOG_NEW, WATCHDOG_OLD) == ''.join(base['cells'][2]['source'])
    assert sum(''.join(c['source']).count('__CONTROLLER_EXPERIMENT_ID__') for c in nb['cells']) == 1
    assert ''.join(nb['cells'][3]['source']).replace(REFERENCE, '').replace(
        METRIC_PROSE_NEW, METRIC_PROSE_OLD
    ).replace(PROTOCOL_NEW, PROTOCOL_OLD) == ''.join(base['cells'][3]['source'])
    assert METRIC_PROSE_NEW in ''.join(nb['cells'][3]['source'])
    assert METRIC_PROSE_OLD not in ''.join(nb['cells'][3]['source'])
    assert PROTOCOL_NEW in ''.join(nb['cells'][3]['source'])
    assert PROTOCOL_OLD not in ''.join(nb['cells'][3]['source'])
    assert ''.join(nb['cells'][4]['source']) == FINAL
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            compile(''.join(cell['source']), '<notebook>', 'exec')
    for mode in ('ok', 'integrity_failure', 'partial', 'corrupt'):
        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            (work / 'exp061').mkdir()
            target = work / 'submission.csv'
            target.write_bytes(b'parent-must-not-be-submitted')
            payload = b'current-input-zon-output'
            (work / 'exp061/submission_zon.csv').write_bytes(payload)
            metrics = {'exp061_deepcenter_tta_integrity_passed': mode != 'integrity_failure',
                       'arm_submission_sha256': {'zon': hashlib.sha256(payload).hexdigest() if mode != 'corrupt' else 'wrong'}}
            (work / 'metrics.json').write_text(json.dumps(metrics))
            g = {'WORKING_DIR': td, 'SUBMISSION_PATH': target,
                 'run_exp061_deepcenter_tta': lambda _: {'arm_status': {'zon': 'skipped' if mode == 'partial' else 'completed'}}}
            try:
                exec(FINAL, g)
            except RuntimeError:
                assert mode != 'ok'
                assert not target.exists()
            else:
                assert mode == 'ok'
                assert target.read_bytes() == payload
    # Execute the ACTUAL reference injection and probe on the established CPU fixture.
    # This verifies orchestration, not GPU numerical equivalence (checked after the run).
    import os
    import numpy as np
    from test_exp061_behavioral import _build_mock_g
    os.environ['BIOHUB_DEEPCENTER_TTA'] = '1'
    os.environ['BIOHUB_VALIDATOR_ENABLE'] = '0'
    for mode in ('ok', 'mismatch', 'reference_exception', 'reference_budget'):
        with tempfile.TemporaryDirectory() as td:
            _, g = _build_mock_g(np, td)
            module = {}
            exec(''.join(nb['cells'][3]['source']), module)
            calls = []
            original_filter = g['filter_output_graph']
            original_heatmap = g['deepcenter_heatmap_for_frame']
            def checked_filter(*args, **kwargs):
                reference = g['deepcenter_heatmap_for_frame'] is original_heatmap
                calls.append(reference)
                if reference and mode == 'reference_exception':
                    raise RuntimeError('reference failure fixture')
                nodes, edges, stats = original_filter(*args, **kwargs)
                if reference and mode == 'mismatch':
                    nodes[next(iter(nodes))]['x'] += 1
                return nodes, edges, stats
            g['filter_output_graph'] = checked_filter
            if mode == 'reference_budget':
                module['EXP061_HARD_STOP_SECONDS'] = 0
            g.update(SUBMISSION_PATH=Path(td) / 'submission.csv',
                     run_exp061_deepcenter_tta=module['run_exp061_deepcenter_tta'])
            Path(g['SUBMISSION_PATH']).write_bytes(b'parent fallback forbidden')
            try:
                exec(FINAL, g)
            except RuntimeError:
                assert mode != 'ok', mode
                assert not Path(g['SUBMISSION_PATH']).exists()
                if mode == 'mismatch':
                    assert json.loads((Path(td) / 'metrics.json').read_text())['checks']['control_parity_sha256_matches_parent'] is False
            else:
                assert mode == 'ok'
                assert calls[:2] == [True, True] and all(c is False for c in calls[2:])
                receipt = json.loads((Path(td) / 'exp061/current_input_reference.json').read_text())
                assert receipt['seconds'] >= 0 and len(receipt['per_dataset_seconds']) == 2
    print('PASS: source parity, controller identity, actual reference-before-patch, mismatch/exception/budget/publication controls')

if __name__ == '__main__':
    validate(sys.argv[1])

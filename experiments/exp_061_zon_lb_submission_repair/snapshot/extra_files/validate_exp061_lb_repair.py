"""Verify the adapter preserves inference and refuses incomplete or corrupt zon output."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from build_exp061_lb_repair import BASE, REFERENCE, FINAL

def validate(path):
    base = json.loads(BASE.read_text(encoding='utf-8'))
    nb = json.loads(Path(path).read_text(encoding='utf-8'))
    assert len(nb['cells']) == len(base['cells'])
    for i in range(3):
        assert nb['cells'][i]['source'] == base['cells'][i]['source']
    assert ''.join(nb['cells'][3]['source']).replace(REFERENCE, '') == ''.join(base['cells'][3]['source'])
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
    print('PASS: unchanged inference/TTA source; current-run publication; integrity/partial/corrupt failure controls')

if __name__ == '__main__':
    validate(sys.argv[1])

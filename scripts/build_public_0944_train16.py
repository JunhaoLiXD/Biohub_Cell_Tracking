"""Instrument the verified 0.944 public inference with frozen train16 validation."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / 'experiments/repro_048_public_0946_exact_copy/snapshot/source/public_0946_edge_feature_tta_copy.ipynb'
DONOR = ROOT / 'experiments/val_039_public_0941_train16/snapshot/source/public_0941_train16.ipynb'
TARGET = ROOT / '.private/current/public_0944_train16.ipynb'
EXPERIMENT = 'val_049_public_0944_train16'

def source(c):
    return ''.join(c['source'])

def cell(s, kind='code'):
    c = dict(cell_type=kind, metadata={}, source=s.splitlines(keepends=True))
    if kind == 'code':
        c.update(outputs=[], execution_count=None)
    return c

def build():
    assert hashlib.sha256(PARENT.read_bytes()).hexdigest() == '4eda3c3dae83f5ad21fee35513aad5f325e09b6de8f77fa55d9b7d6d4b50ca16'
    nb = json.loads(PARENT.read_text(encoding='utf-8'))
    donor = json.loads(DONOR.read_text(encoding='utf-8'))
    s = source(nb['cells'][1])
    old = "'path': checkpoint_path, 'torch': torch"
    new = "'path': checkpoint_path, 'checkpoint_epoch': checkpoint_epoch, 'checkpoint_sha256': _sha256_file(checkpoint_path), 'torch': torch"
    assert s.count(old) == 1
    s = s.replace(old, new)
    # Timer is a separate cell so the parent's future import remains first.
    cells = [cell('# Verified Public 0.944: frozen train16 validation\n\nParent: repro_048. Pretrained inference only. Validation uses the unchanged val_039 selector and scorer. Test bytes must remain exact.\n', 'markdown'), cell('import time as _run_time\nRUN_STARTED_AT = _run_time.perf_counter()\n'), cell(s)]
    pre = source(donor['cells'][9]).replace('bf66c879298e71c5cce0326fbac5956ca567a344ae28f0d402dfc5003fba52bd', '0319ba6d8e864335d3573f6b1a6227c546f17e9247a0c2858fa09b6c2422db3f').replace('repro_038_public_0941_exact_copy', 'repro_048_public_0946_exact_copy').replace('exact repro_038', 'exact repro_048')
    cells.append(cell(pre))
    cells.extend(copy.deepcopy(donor['cells'][10:12]))
    contract = source(donor['cells'][13]).replace('val_039_public_0941_train16', EXPERIMENT).replace('"parent_public_lb": 0.941, "parent_submission_id": 56044403', '"parent_public_lb": 0.944, "parent_submission_id": 56105868')
    cells.append(cell(contract))
    nb['cells'] = cells
    for c in cells:
        if c['cell_type'] == 'code':
            c.update(outputs=[], execution_count=None)
            ast.parse(source(c))
    return nb

if __name__ == '__main__':
    TARGET.write_text(json.dumps(build(), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(TARGET)

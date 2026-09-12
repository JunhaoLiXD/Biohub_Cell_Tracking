"""Verify deterministic adaptation and unchanged selector/scorer source."""
import ast
import json
import sys
from pathlib import Path
from build_public_0944_train16 import build, source, DONOR, PARENT

nb = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
assert nb == build(), 'Source differs from deterministic build'
donor = json.loads(DONOR.read_text(encoding='utf-8'))
assert nb['cells'][4:6] == donor['cells'][10:12], 'Selector/scorer changed'
parent = json.loads(PARENT.read_text(encoding='utf-8'))
original = source(parent['cells'][1])
adapted = source(nb['cells'][2])
assert adapted.replace("'checkpoint_epoch': checkpoint_epoch, 'checkpoint_sha256': _sha256_file(checkpoint_path), ", '') == original
for c in nb['cells']:
    if c['cell_type'] == 'code':
        ast.parse(source(c))
        assert not c['outputs']
assert sum(source(c).count('__CONTROLLER_EXPERIMENT_ID__') for c in nb['cells']) == 1
print(json.dumps(dict(passed=True, inference_preserved=True, frozen_selector_scorer_exact=True)))

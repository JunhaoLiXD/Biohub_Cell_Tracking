"""One gated controller launch. No review waiver, polling or leaderboard action."""
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_controller.core import load_record, verify_snapshot
from experiment_controller.kaggle import launch
folder = ROOT / 'experiments/exp_068_ep015_single_probe'
record = load_record(ROOT, folder.name)
assert record['state'] == 'REVIEWED', 'Only a fresh reviewed, never-launched candidate may start'
assert record['review']['verdict'] == 'PASS' and record['review']['status'] == 'PASSED'
assert not record.get('remote'), 'Never relaunch an existing remote attempt'
verify_snapshot(ROOT, record)
supplement = json.loads((folder / 'admission_supplement_manifest.json').read_text())
for item in supplement['files']:
    assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256']
result = launch(ROOT, folder.name)
print(json.dumps({'state': result['state'], 'remote': result['remote'], 'budget': result['budget']}, indent=2))

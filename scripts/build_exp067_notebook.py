"""Build an unlaunched exp067 notebook from the immutable exp064 parent."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.exp067.patching import patch_notebook, patch_predictor, replay_parent, PARENT_SHA


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['control', 'export', 'decode'], default='control')
    parser.add_argument('--splits', help='explicit JSON train/holdout/test_stems manifest for export')
    parser.add_argument('--checkpoint', default='')
    parser.add_argument('--config')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    stems = []
    if args.mode == 'export':
        if not args.splits:
            parser.error('export mode requires --splits')
        from scripts.exp067.supervise import load_splits
        splits = load_splits(Path(args.splits))
        stems = splits.train + splits.holdout
    config = json.loads(Path(args.config).read_text()) if args.config else {}
    actual = patch_predictor(replay_parent())
    nb = patch_notebook(args.mode, stems, args.checkpoint, config)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(nb, indent=1), encoding='utf-8')
    receipt = {'mode': args.mode, 'parent_sha256': PARENT_SHA, 'notebook_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
               'patched_predictor_sha256': hashlib.sha256(actual.encode()).hexdigest(),
               'real_patch_chain_replayed': True, 'remote_verified': False, 'admission': 'NOT_REQUESTED'}
    path.with_suffix('.build.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()

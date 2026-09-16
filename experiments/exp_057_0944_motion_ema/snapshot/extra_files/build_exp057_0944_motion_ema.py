"""Build exp_057: repro_048 (0.944 edge-feature-TTA bundle) + motion EMA alpha 0.4.

Adds ONLY a per-node velocity EMA to ``motion_relink_edges`` in the repro_048
notebook, gated by ``BIOHUB_MOTION_RELINK_EMA_ALPHA``. The env var defaults ON at
0.4 (``os.environ.setdefault(...)``); an explicit empty string
``BIOHUB_MOTION_RELINK_EMA_ALPHA=''`` disables EMA, and only then is the EMA state
never populated, so every prediction takes the original one-frame path and the
produced submission is byte-identical to repro_048 (SHA256 0319ba6d...). The velocity_um EMA state, source->target propagation, the
``motion_relink_ema_predictions`` / ``motion_relink_one_frame_fallbacks`` counters,
and the fallback semantics match the repro_041 reference
(.private/current/motion_ema_repro_train16.ipynb) line-for-line.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from _bootstrap import PROJECT_ROOT

BASE = PROJECT_ROOT / "experiments/repro_048_public_0946_exact_copy/snapshot/source/public_0946_edge_feature_tta_copy.ipynb"
BASE_SHA256 = "4eda3c3dae83f5ad21fee35513aad5f325e09b6de8f77fa55d9b7d6d4b50ca16"
TARGET = PROJECT_ROOT / ".private/current/exp057_0944_motion_ema.ipynb"

# --- exact anchors (verified count==1 in the base motion_relink_edges cell) ---

CONFIG_FIND = (
    "MOTION_RELINK_VELOCITY_WEIGHT = float(os.environ.get('BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT', '0.5'))\n"
)
CONFIG_REPLACE = (
    "MOTION_RELINK_VELOCITY_WEIGHT = float(os.environ.get('BIOHUB_MOTION_RELINK_VELOCITY_WEIGHT', '0.5'))\n"
    "import time as _exp057_time0\n"
    "_EXP057_CELL_T0 = _exp057_time0.time()\n"
    "os.environ.setdefault('BIOHUB_MOTION_RELINK_EMA_ALPHA', '0.4')\n"
    "MOTION_RELINK_EMA_ALPHA = (\n"
    "    float(os.environ['BIOHUB_MOTION_RELINK_EMA_ALPHA'])\n"
    "    if os.environ.get('BIOHUB_MOTION_RELINK_EMA_ALPHA', '') != ''\n"
    "    else None\n"
    ")\n"
)

INIT_FIND = "    predecessor_position_um: dict[int, np.ndarray] = {}\n"
INIT_REPLACE = (
    "    predecessor_position_um: dict[int, np.ndarray] = {}\n"
    "    velocity_um: dict[int, np.ndarray] = {}\n"
)

PRED_FIND = (
    "            prev_pos = predecessor_position_um.get(source_id)\n"
    "\n"
    "            if prev_pos is None:\n"
    "                predicted = source_pos\n"
    "            else:\n"
    "                predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT * (source_pos - prev_pos)\n"
)
PRED_REPLACE = (
    "            prev_pos = predecessor_position_um.get(source_id)\n"
    "            velocity = velocity_um.get(source_id)\n"
    "\n"
    "            if velocity is not None:\n"
    "                predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT * velocity\n"
    "                stats[\"motion_relink_ema_predictions\"] = stats.get(\"motion_relink_ema_predictions\", 0) + 1\n"
    "            elif prev_pos is None:\n"
    "                predicted = source_pos\n"
    "            else:\n"
    "                predicted = source_pos + MOTION_RELINK_VELOCITY_WEIGHT * (source_pos - prev_pos)\n"
    "                stats[\"motion_relink_one_frame_fallbacks\"] = stats.get(\"motion_relink_one_frame_fallbacks\", 0) + 1\n"
)

UPDATE_FIND = (
    "            predecessor_position_um[target_id] = position_um[source_id]\n"
    "        stats['motion_relink_frames'] += 1\n"
)
UPDATE_REPLACE = (
    "            predecessor_position_um[target_id] = position_um[source_id]\n"
    "            if MOTION_RELINK_EMA_ALPHA is not None:\n"
    "                step_velocity = position_um[target_id] - position_um[source_id]\n"
    "                previous_velocity = velocity_um.get(source_id)\n"
    "                velocity_um[target_id] = (\n"
    "                    step_velocity\n"
    "                    if previous_velocity is None\n"
    "                    else MOTION_RELINK_EMA_ALPHA * step_velocity\n"
    "                    + (1.0 - MOTION_RELINK_EMA_ALPHA) * previous_velocity\n"
    "                )\n"
    "        stats['motion_relink_frames'] += 1\n"
)

# --- Patch 5: append a fail-closed EMA integrity block at the end of the cell ---
# The main pipeline above already wrote SUBMISSION_PATH with EMA ON (default 0.4).
# This block re-runs ONLY the cheap postprocessing over the same on-disk geffs with
# EMA disabled (no second GPU inference), proves the EMA-off submission is
# byte-identical to repro_048 (0319ba6d), requires >=1 canonical edge change, checks
# EMA telemetry, and emits a controller-compatible metrics.json. Any divergence in
# the mirrored off-pass writer makes the off SHA mismatch -> fail-closed (no false
# pass). The main EMA-on candidate path above is left completely unchanged.
APPEND_FIND = (
    "print('Verified progression preserved: 0.933 -> 0.934 -> 0.939 -> 0.941 -> 0.946')"
)
APPEND_BLOCK = '''

# ============================================================================
# exp_057 EMA integrity contract (fail-closed)
# ============================================================================
import hashlib as _exp057_hashlib
import json as _exp057_json
import time as _exp057_time

_exp057_t0 = _exp057_time.time()
_EXP057_REPRO048_SHA256 = '0319ba6d8e864335d3573f6b1a6227c546f17e9247a0c2858fa09b6c2422db3f'
_EXP057_BASE_NB_SHA256 = '4eda3c3dae83f5ad21fee35513aad5f325e09b6de8f77fa55d9b7d6d4b50ca16'
_EXP057_OFF_PATH = WORKING_DIR / 'submission_ema_off.csv'
_exp057_on_alpha = MOTION_RELINK_EMA_ALPHA

def _exp057_read(path):
    _nodes = set(); _edges = []
    with open(path, newline = '') as _f:
        for _row in csv.DictReader(_f):
            if _row['row_type'] == 'edge':
                _edges.append((_row['dataset'], int(_row['source_id']), int(_row['target_id'])))
            elif _row['row_type'] == 'node':
                _nodes.add((_row['dataset'], int(_row['node_id'])))
    return _nodes, _edges

_exp057_ema_predictions = int(sum(int(_r.get('motion_relink_ema_predictions', 0) or 0) for _r in stats_rows))
_exp057_one_frame_fallbacks = int(sum(int(_r.get('motion_relink_one_frame_fallbacks', 0) or 0) for _r in stats_rows))

# EMA-OFF verification pass: same geffs, EMA disabled; writer mirrors the main loop.
MOTION_RELINK_EMA_ALPHA = None
_exp057_off_row_id = 0
with _EXP057_OFF_PATH.open('w', newline = '') as _off_f:
    _off_writer = csv.DictWriter(_off_f, fieldnames = CSV_COLUMNS)
    _off_writer.writeheader()
    for _off_geff in geffs:
        _off_dataset = _off_geff.stem
        _off_graph = graph_from_geff(_off_geff)
        _off_nodes = {}
        for _row in _off_graph.node_attrs().iter_rows(named = True):
            _nid = int(_row['node_id'])
            _off_nodes[_nid] = {'node_id': _nid, 't': int(_row['t']), 'z': float(_row['z']), 'y': float(_row['y']), 'x': float(_row['x'])}
        _off_raw_edges = []
        for _row in _off_graph.edge_attrs().iter_rows(named = True):
            _ep = _row.get('edge_prob') if hasattr(_row, 'get') else None
            _off_raw_edges.append({'source_id': int(_row['source_id']), 'target_id': int(_row['target_id']), 'edge_prob': None if _ep is None else float(_ep)})
        _off_nodes, _off_edges, _off_fstats = filter_output_graph(_off_nodes, _off_raw_edges, dataset = _off_dataset, deepcenter_bundle = DEEPCENTER_VETO_DETECTOR)
        for _nid in sorted(_off_nodes):
            _n = _off_nodes[_nid]
            _off_writer.writerow({'id': _exp057_off_row_id, 'dataset': _off_dataset, 'row_type': 'node', 'node_id': int(_n['node_id']), 't': int(_n['t']), 'z': max(0, int(round(float(_n['z'])))), 'y': max(0, int(round(float(_n['y'])))), 'x': max(0, int(round(float(_n['x'])))), 'source_id': -1, 'target_id': -1})
            _exp057_off_row_id += 1
        for _e in _off_edges:
            _off_writer.writerow({'id': _exp057_off_row_id, 'dataset': _off_dataset, 'row_type': 'edge', 'node_id': -1, 't': -1, 'z': -1, 'y': -1, 'x': -1, 'source_id': int(_e['source_id']), 'target_id': int(_e['target_id'])})
            _exp057_off_row_id += 1
MOTION_RELINK_EMA_ALPHA = _exp057_on_alpha
_exp057_offpass_seconds = _exp057_time.time() - _exp057_t0

_exp057_off_sha = _exp057_hashlib.sha256(_EXP057_OFF_PATH.read_bytes()).hexdigest()
_exp057_on_sha = _exp057_hashlib.sha256(SUBMISSION_PATH.read_bytes()).hexdigest()
_exp057_on_nodes, _exp057_on_edges = _exp057_read(SUBMISSION_PATH)
_exp057_off_nodes, _exp057_off_edges = _exp057_read(_EXP057_OFF_PATH)
_exp057_symdiff = set(_exp057_on_edges) ^ set(_exp057_off_edges)
_exp057_canonical_diff = len(_exp057_symdiff)

_EXP057_EXPECTED_ALPHA = 0.4
_exp057_alpha_ok = (isinstance(_exp057_on_alpha, float) and _exp057_on_alpha == _EXP057_EXPECTED_ALPHA)
_exp057_off_parity = (_exp057_off_sha == _EXP057_REPRO048_SHA256)
_exp057_diff_ok = (_exp057_canonical_diff >= 1)
_exp057_ema_ran = (_exp057_ema_predictions > 0)
_exp057_passed = bool(_exp057_alpha_ok and _exp057_off_parity and _exp057_diff_ok and _exp057_ema_ran)

_exp057_metrics = {
    'schema_version': 1,
    'experiment_id': 'exp_057_0944_motion_ema',
    'primary_metric': float(1.0 if _exp057_passed else 0.0),
    'primary_metric_meaning': 'binary_execution_and_graph_integrity (1.0 pass / 0.0 fail); quality decided by external Public LB',
    'validation': {'protocol': 'public_0944_plus_ema_submission_integrity_lb_probe_v1'},
    'runtime_seconds': float(_exp057_time.time() - _EXP057_CELL_T0),
    'exp057_ema_integrity_passed': _exp057_passed,
    'checks': {
        'effective_on_pass_alpha_is_preregistered_0_4': _exp057_alpha_ok,
        'ema_off_submission_byte_parity_repro048': _exp057_off_parity,
        'canonical_edge_diff_at_least_one': _exp057_diff_ok,
        'ema_predictions_positive': _exp057_ema_ran,
    },
    'effective_motion_relink_ema_alpha': _exp057_on_alpha,
    'effective_motion_relink_velocity_weight': MOTION_RELINK_VELOCITY_WEIGHT,
    'ema_off_submission_sha256': _exp057_off_sha,
    'ema_on_submission_sha256': _exp057_on_sha,
    'candidate_submission_sha256': _exp057_on_sha,
    'repro048_reference_sha256': _EXP057_REPRO048_SHA256,
    'canonical_edge_symdiff_count': _exp057_canonical_diff,
    'motion_relink_ema_predictions': _exp057_ema_predictions,
    'motion_relink_one_frame_fallbacks': _exp057_one_frame_fallbacks,
    'timing': {
        'full_cell_wall_seconds': float(_exp057_time.time() - _EXP057_CELL_T0),
        'gpu_prediction_seconds': float(predict_seconds),
        'ema_off_verification_pass_seconds': float(_exp057_offpass_seconds),
        'note': 'runtime_seconds is the full cell wall time (GPU prediction + on-pass postprocessing/submission + the EMA-off verification pass). The EMA-off pass re-runs postprocessing incl. DeepCenter veto (CUDA), so it is not GPU-free; it is included above.',
    },
    'source_provenance': {
        'base_repro048_notebook_sha256': _EXP057_BASE_NB_SHA256,
        'primary_checkpoint_sha256': _primary_actual_sha256,
        'secondary_checkpoint_sha256': _secondary_actual_sha256,
        'deepcenter_checkpoint_sha256': _deepcenter_actual_sha256,
    },
}
(WORKING_DIR / 'metrics.json').write_text(_exp057_json.dumps(_exp057_metrics, indent = 2, sort_keys = True) + '\\n')
print('exp_057 EMA integrity checks:', _exp057_json.dumps(_exp057_metrics['checks'], sort_keys = True))
print('exp_057 exp057_ema_integrity_passed:', _exp057_passed)
if not _exp057_passed:
    raise AssertionError('exp_057 EMA integrity FAILED (fail-closed): alpha_ok=' + str(_exp057_alpha_ok) + ' effective_alpha=' + str(_exp057_on_alpha) + ' off_sha=' + _exp057_off_sha + ' canonical_diff=' + str(_exp057_canonical_diff) + ' ema_predictions=' + str(_exp057_ema_predictions))
'''

PATCHES = [
    ("config: MOTION_RELINK_EMA_ALPHA", CONFIG_FIND, CONFIG_REPLACE),
    ("init: velocity_um", INIT_FIND, INIT_REPLACE),
    ("prediction: EMA branch", PRED_FIND, PRED_REPLACE),
    ("update: velocity_um propagation", UPDATE_FIND, UPDATE_REPLACE),
    ("append: EMA integrity block", APPEND_FIND, APPEND_FIND + APPEND_BLOCK),
]


def main() -> None:
    raw = BASE.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != BASE_SHA256:
        raise RuntimeError(f"Base repro_048 notebook changed: {actual}")
    nb = json.loads(raw.decode("utf-8"))

    cell = None
    for c in nb["cells"]:
        if c["cell_type"] == "code" and "def motion_relink_edges" in "".join(c["source"]):
            cell = c
            break
    if cell is None:
        raise RuntimeError("motion_relink_edges cell not found")

    src = "".join(cell["source"])
    for name, find, replace in PATCHES:
        n = src.count(find)
        if n != 1:
            raise RuntimeError(f"Patch '{name}' anchor count is {n}, expected 1")
        src = src.replace(find, replace)
    # Store as a single source string (Jupyter accepts str or list).
    cell["source"] = src

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(
        json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    out_sha = hashlib.sha256(TARGET.read_bytes()).hexdigest()
    print(f"Built {TARGET.relative_to(PROJECT_ROOT)}")
    print(f"Base SHA256 : {BASE_SHA256}")
    print(f"exp057 SHA256: {out_sha}")
    print("Applied patches:", ", ".join(name for name, _, _ in PATCHES))


if __name__ == "__main__":
    main()

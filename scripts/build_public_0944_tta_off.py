"""Build the matched TTA-off arm directly from frozen val_049."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / 'experiments/val_049_public_0944_train16/snapshot/source/public_0944_train16.ipynb'
TARGET = ROOT / '.private/current/public_0944_tta_off.ipynb'
EXPERIMENT = 'exp_050_public_0944_tta_off'

def source(cell):
    return ''.join(cell['source'])

def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Expected one frozen source anchor: ' + old[:100])
    return text.replace(old, new, 1)

EXPORT_HELPER = '''
import gzip as _graph_gzip
FINAL_GRAPH_MANIFEST = {}
def valid_tta_off_receipts(receipts):
    return (bool(receipts) and {r.get("phase") for r in receipts} == {"test", "validation"}
            and all(r.get("enabled") is False and r.get("views") == 8 for r in receipts))

def export_scored_graph(stem, pred_nodes, pred_edges, gt_nodes, gt_edges, t_true, row):
    payload = {
        "schema_version": 1, "stem": stem, "graph_stage": "final_scored_after_linefit",
        "pred_nodes": [[int(n), int(v[0]), *[float(x) for x in v[1:]]] for n, v in sorted(pred_nodes.items())],
        "pred_edges": [[int(s), int(t)] for s, t in pred_edges],
        "gt_nodes": [[int(n), int(v[0]), *[float(x) for x in v[1:]]] for n, v in sorted(gt_nodes.items())],
        "gt_edges": [[int(s), int(t)] for s, t in gt_edges],
        "t_true": float(t_true), "score_row": row,
    }
    # Strict serialization exercises every exported numeric field before writing.
    raw = json.dumps(payload, sort_keys=True, allow_nan=False).encode("utf-8")
    path = WORKING_DIR / "final_validation_graphs" / (stem + ".json.gz")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_graph_gzip.compress(raw, mtime=0))
    return {"path": str(path), "sha256": _sha256_file(path),
            "nodes": len(pred_nodes), "edges": len(pred_edges)}
'''

def build():
    manifest = json.loads((PARENT.parents[1] / 'manifest.json').read_text())
    expected = next(r['sha256'] for r in manifest['files'] if r.get('role') == 'source_notebook')
    if hashlib.sha256(PARENT.read_bytes()).hexdigest() != expected:
        raise ValueError('Frozen val_049 source hash mismatch')
    nb = json.loads(PARENT.read_text(encoding='utf-8'))
    nb = copy.deepcopy(nb)
    nb['cells'][0]['source'] = ['# Matched feature-TTA off control\n\n',
        'Behavior parent: val_049_public_0944_train16 (B). This is matched arm A.\n',
        'Only algorithmic change: BIOHUB_EDGE_FEATURE_TTA 1 to 0. Detection D4 TTA, upstream motion and all weights remain frozen.\n',
        'Frozen train16 screening only. Contract KEEP means a valid attribution arm, not quality improvement. No leaderboard submission or promotion.\n']
    s = source(nb['cells'][2])
    s = replace_once(s, "os.environ['BIOHUB_EDGE_FEATURE_TTA'] = '1'", "os.environ['BIOHUB_EDGE_FEATURE_TTA'] = '0'\nos.environ['BIOHUB_AUDIT_PHASE'] = 'test'")
    # This text lies inside the patch string executed in each prediction worker.
    anchor = "    if _edge_tta:\n        if _unet_acc.shape != unet_out.shape:"
    telemetry = '''    # Read-only receipt from the executed D4 branch, one file per worker.
    with open('/kaggle/working/edge_tta_execution_' + str(os.getpid()) + '.jsonl', 'a') as _audit_file:
        _audit_file.write(__import__('json').dumps({'phase': os.environ['BIOHUB_AUDIT_PHASE'], 'enabled': bool(_edge_tta), 'views': int(_nv)}, allow_nan=False) + chr(10))

'''
    s = replace_once(s, anchor, telemetry + anchor)
    s = replace_once(s, "print('Edge-feature TTA patch installed and enabled')", "print('Edge-feature TTA patch installed; effective flag:', os.environ['BIOHUB_EDGE_FEATURE_TTA'])\n(WORKING_DIR / 'executed_predict_unet_transformer.py').write_text(_ps.read_text(), encoding='utf-8')")
    s = s.replace("'verified_public_lb_0946'", "'matched_tta_off_unscored'")
    s = s.replace("print('Verified progression preserved: 0.933 -> 0.934 -> 0.939 -> 0.941 -> 0.946')", "print('Matched TTA-off control completed; no leaderboard score claimed')")
    nb['cells'][2]['source'] = s.splitlines(keepends=True)
    s = source(nb['cells'][3])
    s = replace_once(s, "EXPECTED_SUBMISSION_SHA = '0319ba6d8e864335d3573f6b1a6227c546f17e9247a0c2858fa09b6c2422db3f'", "EXPECTED_SUBMISSION_SHA = _sha256_file(SUBMISSION_PATH)\nTEST_FINISHED_AT = _run_time.perf_counter()\nTEST_EXECUTED_SOURCE_SHA = _sha256_file(_ps)")
    s = replace_once(s, '"submission_sha256_exact": _sha256_file(SUBMISSION_PATH) == EXPECTED_SUBMISSION_SHA,', '"test_submission_recorded": len(EXPECTED_SUBMISSION_SHA) == 64,\n    "edge_feature_tta_disabled": os.environ.get("BIOHUB_EDGE_FEATURE_TTA") == "0",')
    s = replace_once(s, '"parent": "repro_048_public_0946_exact_copy",', '"parent": "val_049_public_0944_train16",')
    s = replace_once(s, 'print("Inference identity PASS: exact repro_048 submission and actual epoch-2 checkpoint")', 'print("Inference identity PASS: matched TTA-off arm and actual epoch-2 checkpoint")\nos.environ["BIOHUB_AUDIT_PHASE"] = "validation"')
    nb['cells'][3]['source'] = s.splitlines(keepends=True)
    # Cell 4 (selection/inference) is byte-for-byte frozen. Scoring functions in
    # cell 5 remain exact; graph serialization follows the completed score call.
    s = source(nb['cells'][5])
    s = EXPORT_HELPER + '\n' + s
    anchor = '        rows_this_config.append(row)\n'
    s = replace_once(s, anchor, '        FINAL_GRAPH_MANIFEST[stem] = export_scored_graph(stem, pred_nodes_plain, pred_edges_plain, gt_nodes_plain, gt_edges_plain, t_true, row)\n' + anchor)
    nb['cells'][5]['source'] = s.splitlines(keepends=True)
    s = source(nb['cells'][6]).replace('val_049_public_0944_train16', EXPERIMENT)
    insert = '''_tta_receipts = []
for _receipt_path in sorted(WORKING_DIR.glob("edge_tta_execution_*.jsonl")):
    _tta_receipts.extend(json.loads(line) for line in _receipt_path.read_text().splitlines())
_tta_counts = {phase: sum(r["phase"] == phase for r in _tta_receipts) for phase in ("test", "validation")}
_checks.update({
    "executed_tta_off_both_splits": valid_tta_off_receipts(_tta_receipts),
    "executed_source_unchanged": _sha256_file(_ps) == TEST_EXECUTED_SOURCE_SHA == _sha256_file(WORKING_DIR / "executed_predict_unet_transformer.py"),
    "final_graph_exports_complete": set(FINAL_GRAPH_MANIFEST) == set(val_stems) and all(FINAL_GRAPH_MANIFEST[r["stem"]]["nodes"] == r["t_pred"] for r in validator_sample_rows),
})
_parent_score = 0.9310696298996892
_tta_effect_b_minus_a = _parent_score - float(_summary["proxy_score"])
'''
    s = replace_once(s, '_metrics = {\n', insert + '_metrics = {\n')
    s = s.replace('"selection_and_scorer_reference": "val_008_public_0933_train16_launchable"', '"selection_and_scorer_reference": "val_039_public_0941_train16"')
    s = replace_once(s, '"baseline_establishment_only": True,', '''"attribution_arm_only": True,
        "arm": "A", "comparison_arm": "B=val_049_public_0944_train16",
        "tta_effect_b_minus_a": _tta_effect_b_minus_a,
        "tta_nonnegative_screen": _tta_effect_b_minus_a >= 0.0,
        "quality_advancement_authorized": False,
        "edge_tta_execution_counts": _tta_counts,
        "executed_source_sha256": TEST_EXECUTED_SOURCE_SHA,
        "final_graph_manifest": FINAL_GRAPH_MANIFEST,
        "timing_seconds": {"test_and_setup": TEST_FINISHED_AT - RUN_STARTED_AT,
                           "test_predict": float(predict_seconds), "validation_predict": float(predict_val_seconds),
                           "validation_and_scoring": _run_time.perf_counter() - TEST_FINISHED_AT},''')
    s = s.replace('json.dumps(_metrics, indent=2, sort_keys=True)', 'json.dumps(_metrics, indent=2, sort_keys=True, allow_nan=False)')
    nb['cells'][6]['source'] = s.splitlines(keepends=True)
    for c in nb['cells']:
        if c['cell_type'] == 'code':
            c.update(outputs=[],execution_count=None)
            ast.parse(source(c))
    return nb

if __name__ == '__main__':
    TARGET.write_text(json.dumps(build(),ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print(TARGET)

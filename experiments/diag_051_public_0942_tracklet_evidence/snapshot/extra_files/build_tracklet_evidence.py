"""Build one behavior-preserving evidence export from immutable repro_041."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = 'diag_051_public_0942_tracklet_evidence'
PARENT = ROOT / 'experiments/repro_041_public_0941_motion_ema/snapshot/source/public_0941_ema_repro.ipynb'
TARGET = ROOT / '.private/current/public_0942_tracklet_evidence.ipynb'

def source(cell):
    return ''.join(cell['source'])

def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Frozen anchor mismatch: ' + repr(old[:110]))
    return text.replace(old, new, 1)

def patch_predictor(text):
    text = once(text, '    zarr_arr = ', '    _ev_begin(ds_path)\n    zarr_arr = ')
    anchor = '            if secondary_model is not None:\n                if secondary_unet_out is None:'
    text = once(text, anchor, '            _ev_primary_logits = _ev_primary(edge_logits_pair)\n' + anchor)
    text = once(text, '        del unet_out\n', '            _ev_pair(locals())\n\n        del unet_out\n')
    text = once(text, '    if edges:\n        graph.add_edge_attr_key',
                '    _ev_nodes(coords, node_ids)\n\n    if edges:\n        graph.add_edge_attr_key')
    helper = (ROOT / 'scripts/tracklet_evidence_worker.py').read_text(encoding='utf-8')
    text = once(text, 'if __name__ == "__main__":', helper + '\n\nif __name__ == "__main__":')
    ast.parse(text)
    return text

def build():
    manifest = json.loads((PARENT.parents[1] / 'manifest.json').read_text())
    expected = next(r['sha256'] for r in manifest['files'] if r.get('role') == 'source_notebook')
    assert hashlib.sha256(PARENT.read_bytes()).hexdigest() == expected
    nb = json.loads(PARENT.read_text(encoding='utf-8'))
    nb['cells'][0]['source'] = [
        '# Retained EMA reference: tracklet evidence diagnostic\n\n',
        'Actual behavior parent: repro_041_public_0941_motion_ema. One read-only export run ',
        'supports the NEXT_RESEARCH_PRIORITIES reachable-error audit before longer-context association. ',
        'No training or inference change. Exact parent submission and validation CSV bytes are gates. ',
        'Embedding cache uses the existing two-frame encoder in overlapping windows; it does not ',
        'claim five-frame encoding. Offline composition can inspect five-frame tracklet context. ',
        'GT is exported only after prediction for offline analysis. No leaderboard submission.\n']
    # Install hooks after all frozen source patches; no worker is started before this.
    patch_body = ast.get_source_segment(Path(__file__).read_text(), next(
        n for n in ast.parse(Path(__file__).read_text()).body
        if isinstance(n, ast.FunctionDef) and n.name == 'patch_predictor'))
    helper = (ROOT / 'scripts/tracklet_evidence_worker.py').read_text(encoding='utf-8')
    patch_body = patch_body.replace("(ROOT / 'scripts/tracklet_evidence_worker.py').read_text(encoding='utf-8')", repr(helper))
    once_body = ast.get_source_segment(Path(__file__).read_text(), next(
        n for n in ast.parse(Path(__file__).read_text()).body
        if isinstance(n, ast.FunctionDef) and n.name == 'once'))
    for c in nb['cells']:
        if c['cell_type'] != 'code':
            continue
        s = source(c)
        if 'def list_test_stems()' in s:
            install = '\nimport ast\n' + once_body + '\n' + patch_body + '\n'
            install += "os.environ['BIOHUB_TRACKLET_EVIDENCE'] = 'off'\n_ps.write_text(patch_predictor(_ps.read_text()), encoding='utf-8')\n(WORKING_DIR / 'executed_predict_unet_transformer.py').write_text(_ps.read_text(), encoding='utf-8')\n"
            s = once(s, 'def list_test_stems()', install + '\ndef list_test_stems()')
        if 'def filter_output_graph(' in s:
            s = (ROOT / 'scripts/tracklet_evidence_graphs.py').read_text() + '\n' + s
            anchors = [
                ('    if OUTPUT_MOTION_RELINK:\n', "    _ev_graph(dataset, 'distance_filtered', nodes_by_id, edges)\n"),
                ('    if OUTPUT_SINGLE_PARENT_REPAIR and edges:\n', "    _ev_graph(dataset, 'motion_relinked', nodes_by_id, edges)\n"),
                ('    repair_frame_cache: dict[int, np.ndarray] = {}\n', "    _ev_graph(dataset, 'degree_repaired', nodes_by_id, edges)\n"),
                ('    nodes_by_id, edges = recover_strict_gap2(', "    _ev_graph(dataset, 'gap1', nodes_by_id, edges)\n"),
                ('    edges = add_safe_divisions_postlink(\n', "    _ev_graph(dataset, 'gap2', nodes_by_id, edges)\n"),
                ("    _geo_cands = stats['safe_division_geometric_candidates']\n", "    _ev_graph(dataset, 'safe_divisions', nodes_by_id, edges)\n"),
                ('    nodes_by_id, edges = filter_short_track_components(nodes_by_id, edges, stats)\n', "    _ev_graph(dataset, 'geometry_and_isolated', nodes_by_id, edges)\n"),
                ('    nodes_by_id = linefit_smooth_output_graph(nodes_by_id, edges, stats)\n', "    _ev_graph(dataset, 'short_track_filtered', nodes_by_id, edges)\n"),
            ]
            for anchor, hook in anchors:
                s = once(s, anchor, hook + anchor)
        if 'predict_val_seconds = None' in s:
            s = "EV_ENABLED = True\nos.environ['BIOHUB_TRACKLET_EVIDENCE'] = 'validation'\n" + s
        if 'def score_sample(' in s:
            s = once(s, '        _real_test_dir = TEST_DIR\n', "        _ev_graph(stem, 'raw_post_ilp', raw_nodes_by_id, raw_edges)\n        _real_test_dir = TEST_DIR\n")
            s = once(s, '        rows_this_config.append(row)\n', '        _ev_final(stem, pred_nodes_plain, pred_edges_plain, gt_nodes_plain, gt_edges_plain, t_true, row)\n        rows_this_config.append(row)\n')
            anchor = '    p2g, g2p = match_nodes_bipartite(pred_nodes_plain, gt_nodes_plain, max_dist=VALIDATOR_MATCH_RADIUS_UM)\n'
            s = once(s, anchor, anchor + "    _ev_json(stem, 'scorer_matching', dict(p2g=list(p2g.items()), g2p=list(g2p.items())))\n")
        if 'REPRO_EXPECTED = ' in s:
            s = s.replace('_EXPERIMENT_ID == "repro_041_public_0941_motion_ema"', f'_EXPERIMENT_ID == "{EXPERIMENT}"')
            s = s.replace('"one_time_post_run_claude_review_required": True', '"one_time_post_run_claude_review_required": False')
            s = s.replace('"post_run_claude_review_status": "PENDING"', '"post_run_claude_review_status": "NOT_REQUIRED"')
            s = s.replace('"reproduction_reference": "exp_040_public_0941_motion_ema"', '"reproduction_reference": "repro_041_public_0941_motion_ema"')
            contract = (ROOT / 'scripts/tracklet_evidence_contract.py').read_text()
            s = once(s, '(WORKING_DIR / "validation_stage_stats.json").write_text(', contract + '\n(WORKING_DIR / "validation_stage_stats.json").write_text(')
            s = s.replace('json.dumps(_metrics, indent=2, sort_keys=True)', 'json.dumps(_metrics, indent=2, sort_keys=True, allow_nan=False)')
        c['source'] = s.splitlines(keepends=True)
        c.update(outputs=[], execution_count=None)
        ast.parse(s)
    return nb

if __name__ == '__main__':
    TARGET.write_text(json.dumps(build(), ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(TARGET)

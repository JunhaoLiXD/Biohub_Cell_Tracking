"""Exact telemetry injections + analysis cell for exp_058 A0 division diagnostic.

Consumed by scripts/build_exp058_a0_division_diagnostic.py. Every candidate/deepcenter
injection is PURELY ADDITIVE: `replacements()` (functions cell) and `cell5_replacements()`
(validator-loop cell) return (anchor, replacement) pairs where the replacement is the
anchor with extra `# __EXP058_TELEMETRY__`-tagged lines inserted; the builder asserts
that stripping the tagged lines reproduces the anchor and the base cell byte-for-byte.

SCORER FINDING (2026-09-16): val_049 scores with its OWN inline functions in cell 5
(match_nodes_bipartite / compute_edge_confusion / compute_division_confusion /
score_sample / aggregate_official), NOT biohub_tracking.division_metrics. The official
3/8/9 and 0.9310696 come from those. The analysis cell reuses the notebook's own scorer
and the per-stem graphs stashed during the validator loop.
"""
from __future__ import annotations

TAG = "  # __EXP058_TELEMETRY__"


def _tag(line: str) -> str:
    return line + TAG


TELEMETRY_INIT = "\n".join([
    "import time as _exp058_time",
    "_EXP058_T0 = _exp058_time.time()",
    "_EXP058_LOG = {'candidates': [], 'deepcenter': [], 'graphs': {}}",
    "def _exp058_native(v):",
    "    if isinstance(v, bool): return bool(v)",
    "    try:",
    "        import numpy as _np",
    "        if isinstance(v, _np.integer): return int(v)",
    "        if isinstance(v, _np.floating): return float(v)",
    "    except Exception: pass",
    "    if isinstance(v, (list, tuple)): return [_exp058_native(_x) for _x in v]",
    "    if isinstance(v, (int, float, str, type(None))): return v",
    "    return float(v) if hasattr(v, '__float__') else str(v)",
    "def _exp058_log_cand(stage, **kw):",
    "    rec = {'stage': str(stage)}",
    "    for _k, _v in kw.items(): rec[_k] = _exp058_native(_v)",
    "    _EXP058_LOG['candidates'].append(rec)",
    "def _exp058_log_dc(dataset, t, point, score, prefix):",
    "    _EXP058_LOG['deepcenter'].append({'dataset': None if dataset is None else str(dataset), 't': int(t), 'point': [float(point[0]), float(point[1]), float(point[2])], 'score': None if score is None else float(score), 'prefix': str(prefix)})",
])


def replacements():
    """(anchor, replacement) pairs for the FUNCTIONS cell (cell 2)."""
    r: list[tuple[str, str]] = []

    anchor0 = "def deepcenter_accept_repair_point"
    init_block = "\n".join(_tag(l) for l in TELEMETRY_INIT.splitlines())
    r.append((anchor0, init_block + "\n" + anchor0))

    def add_after(anchor: str, after_line: str, tagged_line: str) -> None:
        assert anchor.count(after_line) == 1, after_line
        r.append((anchor, anchor.replace(after_line, after_line + "\n" + tagged_line, 1)))

    I16, I20, I24 = " " * 16, " " * 20, " " * 24
    common = "dataset=dataset, t=t, source_id=source_id, candidate_id=candidate_id, existing_child_id=existing_child_id, child_dist=child_dist, parent_dist=parent_dist"

    a = f"{I16}if parent_dist > SAFE_DIV_MAX_UM:\n{I20}continue"
    add_after(a, f"{I16}if parent_dist > SAFE_DIV_MAX_UM:",
              _tag(f"{I20}_exp058_log_cand('parent_dist_gt_max', {common})"))

    a = f"{I16}if sister_dist > SAFE_DIV_SISTER_MAX_UM:\n{I20}continue"
    add_after(a, f"{I16}if sister_dist > SAFE_DIV_SISTER_MAX_UM:",
              _tag(f"{I20}_exp058_log_cand('sister_dist_gt_max', {common}, sister_dist=sister_dist)"))

    a = (f"{I16}if SAFE_DIV_REQUIRE_MUTUAL_NN and candidate_id != mutual_nn_id:\n"
         f"{I20}stats['safe_division_mutual_nn_rejected'] += 1\n{I20}continue")
    add_after(a, f"{I20}stats['safe_division_mutual_nn_rejected'] += 1",
              _tag(f"{I20}_exp058_log_cand('mutual_nn', {common}, sister_dist=sister_dist)"))

    a = (f"{I20}if len(c1_succ) != 1 or len(q_succ) != 1:\n"
         f"{I24}stats['safe_division_divergence_rejected'] += 1\n{I24}continue")
    add_after(a, f"{I20}if len(c1_succ) != 1 or len(q_succ) != 1:",
              _tag(f"{I24}_exp058_log_cand('divergence_succ_count', {common}, sister_dist=sister_dist)"))

    a = (f"{I20}if c1_grandchild is None or q_grandchild is None or int(c1_grandchild['t']) != t + 2 or (int(q_grandchild['t']) != t + 2):\n"
         f"{I24}stats['safe_division_divergence_rejected'] += 1\n{I24}continue")
    add_after(a, f"{I20}if c1_grandchild is None or q_grandchild is None or int(c1_grandchild['t']) != t + 2 or (int(q_grandchild['t']) != t + 2):",
              _tag(f"{I24}_exp058_log_cand('divergence_grandchild_t2', {common}, sister_dist=sister_dist)"))

    a = (f"{I20}if grandchild_dist - sister_dist < SAFE_DIV_DIVERGE_UM:\n"
         f"{I24}stats['safe_division_divergence_rejected'] += 1\n{I24}continue")
    add_after(a, f"{I20}if grandchild_dist - sister_dist < SAFE_DIV_DIVERGE_UM:",
              _tag(f"{I24}_exp058_log_cand('divergence_um', {common}, sister_dist=sister_dist, grandchild_dist=grandchild_dist)"))

    # geometric-ok: record ALL geometric candidates (incl. candidate time + position
    # so the DeepCenter score, taken at candidate time t+1, joins correctly)
    a = f"{I16}stats['safe_division_geometric_candidates'] += 1"
    r.append((a, a + "\n" + _tag(f"{I16}_exp058_log_cand('geometric_ok', {common}, sister_dist=sister_dist, cand_t=int(candidate['t']), point=node_point(candidate))")))

    a = (f"{I16}if DEEPCENTER_SAFE_DIV_VETO and (not deepcenter_accept_repair_point(dataset, int(candidate['t']), node_point(candidate), deepcenter_bundle, frame_cache, deepcenter_cache, stats, 'safe_div', DEEPCENTER_SAFE_DIV_THRESHOLD)):\n"
         f"{I20}continue")
    add_after(a, f"{I16}if DEEPCENTER_SAFE_DIV_VETO and (not deepcenter_accept_repair_point(dataset, int(candidate['t']), node_point(candidate), deepcenter_bundle, frame_cache, deepcenter_cache, stats, 'safe_div', DEEPCENTER_SAFE_DIV_THRESHOLD)):",
              _tag(f"{I20}_exp058_log_cand('deepcenter_veto', {common}, sister_dist=sister_dist)"))

    a = (f"{I20}if abs(child_dist - parent_dist) / symmetry_denominator > SAFE_DIV_SISTER_SYMMETRY_TAU:\n"
         f"{I24}stats['safe_division_symmetry_rejected'] += 1\n{I24}continue")
    add_after(a, f"{I20}if abs(child_dist - parent_dist) / symmetry_denominator > SAFE_DIV_SISTER_SYMMETRY_TAU:",
              _tag(f"{I24}_exp058_log_cand('symmetry', {common}, sister_dist=sister_dist)"))

    a = f"{I16}proposals.append((score, source_id, candidate_id, parent_dist, sister_dist))"
    r.append((a, a + "\n" + _tag(f"{I16}_exp058_log_cand('accepted_proposal', {common}, sister_dist=sister_dist, score=score)")))

    a = "            added.append({'source_id': source_id, 'target_id': candidate_id, 'edge_prob': None, 'distance_um': parent_dist, 'safe_division': 1})"
    r.append((a, a + "\n" + _tag("            _exp058_log_cand('added_final', dataset=dataset, t=t, source_id=source_id, candidate_id=candidate_id, parent_dist=parent_dist)")))

    a = "    score = deepcenter_score_point(dataset, int(t), point, detector_bundle, frame_cache, heatmap_cache)"
    r.append((a, a + "\n" + _tag("    _exp058_log_dc(dataset, int(t), point, score, prefix)")))

    # --- source-level gates (before the candidate loop) ---
    a = f"{' '*12}if existing_child is None or int(existing_child['t']) != t + 1:\n{' '*16}continue"
    add_after(a, f"{' '*12}if existing_child is None or int(existing_child['t']) != t + 1:",
              _tag(f"{' '*16}_exp058_log_cand('source_no_existing_child_at_t1', dataset=dataset, t=t, source_id=source_id, existing_child_id=existing_child_id)"))

    a = f"{' '*12}if child_dist > SAFE_DIV_EXISTING_CHILD_MAX_UM:\n{' '*16}continue"
    add_after(a, f"{' '*12}if child_dist > SAFE_DIV_EXISTING_CHILD_MAX_UM:",
              _tag(f"{' '*16}_exp058_log_cand('source_existing_child_too_far', dataset=dataset, t=t, source_id=source_id, existing_child_id=existing_child_id, child_dist=child_dist)"))

    # --- frame-level eligibility counts (after source/candidate pools built) ---
    a = f"{' '*8}candidate_ids = [node_id for node_id in child_frame_ids if node_id not in incoming and node_id not in used_targets]"
    r.append((a, a + "\n" + _tag(f"{' '*8}_exp058_log_cand('frame_pools', dataset=dataset, t=t, n_frame_sources=len(ids_by_t[t]), n_eligible_sources=len(source_ids), n_candidates=len(candidate_ids), n_child_frame=len(child_frame_ids))")))

    # --- cap / conflict outcomes (second, selection loop) ---
    a = (f"{' '*12}if len(added) >= global_cap:\n{' '*16}stats['safe_division_skipped_cap'] += 1\n{' '*16}break")
    add_after(a, f"{' '*16}stats['safe_division_skipped_cap'] += 1",
              _tag(f"{' '*16}_exp058_log_cand('cap_global', dataset=dataset, t=t, source_id=source_id, candidate_id=candidate_id, global_cap=global_cap)"))

    a = (f"{' '*12}if added_this_frame >= frame_cap:\n{' '*16}break")
    add_after(a, f"{' '*12}if added_this_frame >= frame_cap:",
              _tag(f"{' '*16}_exp058_log_cand('cap_frame', dataset=dataset, t=t, source_id=source_id, candidate_id=candidate_id, frame_cap=frame_cap)"))

    a = (f"{' '*12}if candidate_id in used_targets or candidate_id in incoming:\n{' '*16}continue")
    add_after(a, f"{' '*12}if candidate_id in used_targets or candidate_id in incoming:",
              _tag(f"{' '*16}_exp058_log_cand('conflict_target', dataset=dataset, t=t, source_id=source_id, candidate_id=candidate_id)"))

    a = (f"{' '*12}if source_id in used_sources:\n{' '*16}continue")
    add_after(a, f"{' '*12}if source_id in used_sources:",
              _tag(f"{' '*16}_exp058_log_cand('conflict_source', dataset=dataset, t=t, source_id=source_id, candidate_id=candidate_id)"))

    # --- DeepCenter missing => fail-OPEN bypass (record distinctly) ---
    a = f"    if detector_bundle is None or dataset is None:\n        stats[f'deepcenter_{{prefix}}_missing'] += 1\n        return True"
    add_after(a, f"        stats[f'deepcenter_{{prefix}}_missing'] += 1",
              _tag("        _exp058_log_dc(dataset, int(t), point, None, str(prefix) + '_missing_bypass')"))

    a = f"    if score is None:\n        stats[f'deepcenter_{{prefix}}_missing'] += 1\n        return True"
    add_after(a, f"        stats[f'deepcenter_{{prefix}}_missing'] += 1",
              _tag("        _exp058_log_dc(dataset, int(t), point, None, str(prefix) + '_missing_bypass')"))

    return r


def cell5_replacements():
    """(anchor, replacement) pairs for the VALIDATOR-LOOP cell (cell 5): stash the
    per-stem plain graphs + score row so the analysis cell can reuse them."""
    anchor = "        validator_sample_rows.append(row)"
    stash = _tag("        _EXP058_LOG['graphs'][stem] = {'pred_nodes': dict(pred_nodes_plain), 'pred_edges': list(pred_edges_plain), 'gt_nodes': dict(gt_nodes_plain), 'gt_edges': list(gt_edges_plain), 't_true': t_true, 'row': dict(row)}")
    return [(anchor, anchor + "\n" + stash)]


# ---------------------------------------------------------------------------
# Analysis + integrity cell (appended as a NEW, separate cell; not parity-guarded).
# Uses the notebook's OWN inline scorer (match_nodes_bipartite, score_sample,
# aggregate_official) and the stashed per-stem graphs.
# ---------------------------------------------------------------------------
ANALYSIS_INTEGRITY_CELL = r'''# === exp_058 A0 division diagnostic: analysis + integrity ===
import json as _json, hashlib as _hashlib, pathlib as _pathlib
_OUT = _pathlib.Path('/kaggle/working')
_EXP_SHA = '0319ba6d8e864335d3573f6b1a6227c546f17e9247a0c2858fa09b6c2422db3f'
_EXP_SCORE = 0.9310696298996892
_EXP_DIV = (3, 8, 9)
_RUNTIME_CEILING_S = 1.4 * 3600.0
_GT_DIVISIONS_EXPECTED = 12  # 44b6 (tp1+fn4=5) + 6bba (tp2+fn5=7) on the frozen panel
_STAGE_ORDER = ['source_no_existing_child_at_t1', 'source_existing_child_too_far',
    'parent_dist_gt_max', 'sister_dist_gt_max', 'mutual_nn',
    'divergence_succ_count', 'divergence_grandchild_t2', 'divergence_um',
    'geometric_ok', 'deepcenter_veto', 'symmetry', 'accepted_proposal',
    'conflict_target', 'conflict_source', 'cap_frame', 'cap_global', 'added_final']
_ORD = {s: i for i, s in enumerate(_STAGE_ORDER)}
_REACH_STAGES = set(_STAGE_ORDER)  # per-candidate terminal/label stages

_graphs = _EXP058_LOG['graphs']
_cands = _EXP058_LOG['candidates']
_dcs = _EXP058_LOG['deepcenter']


def _dump_jsonl(name, recs):
    with (_OUT / name).open('w', encoding='utf-8') as _f:
        for _r in recs:
            _f.write(_json.dumps(_r) + '\n')

_dump_jsonl('exp058_candidate_journey.jsonl', _cands)
_dump_jsonl('exp058_deepcenter_scores.jsonl', _dcs)


def _out_map(edges):
    m = {}
    for _s, _t in edges:
        m.setdefault(_s, set()).add(_t)
    return m

# per-stem candidate index (grouped by source, and per (source,candidate) journeys)
_cands_by_stem = {}
for _c in _cands:
    _cands_by_stem.setdefault(_c.get('dataset'), []).append(_c)

# ---- 1) reproduce the official aggregate from the stashed rows (non-perturbation) ----
# NOTE (integrity design, reconciled w/ Codex): non-perturbation is proven by TWO layers:
#  (a) BUILD-TIME parity guard: stripping every telemetry-tagged line reproduces the base
#      cells byte-for-byte => instrumentation is purely additive (cannot mutate graph state);
#  (b) RUNTIME exact reproduction here of the official proxy 0.9310696, division 3/8/9, and
#      the test submission SHA 0319ba6d. If telemetry had perturbed anything these would differ.
# This replaces the earlier over-promised "intermediate-graph shadow parity" claim.
_rows = [g['row'] for g in _graphs.values()]
_official = aggregate_official(_rows) if _rows else {}
_off_div = (int(_official.get('div_tp', -1)), int(_official.get('div_fp', -1)), int(_official.get('div_fn', -1)))
_official_ok = bool(_rows) and abs(float(_official.get('proxy_score', -1)) - _EXP_SCORE) < 1e-9 and _off_div == _EXP_DIV and len(_graphs) == 16

# per-specimen aggregates (also feed specimen_metrics for the controller contract)
_by_spec = {}
for _stem, _g in _graphs.items():
    _by_spec.setdefault(_stem.split('_')[0], []).append(_g['row'])
_spec_official = {_sp: aggregate_official(_rs) for _sp, _rs in _by_spec.items()}

# ---- 2) test submission SHA256 (non-perturbation of the real test path) ----
_sub = _OUT / 'submission.csv'
_sub_sha = _hashlib.sha256(_sub.read_bytes()).hexdigest() if _sub.exists() else None
_sha_ok = _sub_sha == _EXP_SHA

# ---- 3) P2: GT-centric coverage table -- one row per GT division, "first missing" cause ----
_coverage = []
_gt_div_total = 0
for _stem, _g in _graphs.items():
    _pn, _pe, _gn, _ge = _g['pred_nodes'], _g['pred_edges'], _g['gt_nodes'], _g['gt_edges']
    _p2g, _g2p = match_nodes_bipartite(_pn, _gn, max_dist=VALIDATOR_MATCH_RADIUS_UM)
    _gt_out = _out_map(_ge)
    _pred_out = _out_map(_pe)
    _gt_div_sources = [s for s, o in _gt_out.items() if len(o) >= 2]
    _gt_div_total += len(_gt_div_sources)
    _by_src = {}
    for _c in _cands_by_stem.get(_stem, []):
        _by_src.setdefault(_c.get('source_id'), []).append(_c)
    for _gsrc in _gt_div_sources:
        _ps = _g2p.get(_gsrc)               # g2p: GT node -> matched PRED node
        _rec = {'stem': _stem, 'gt_source': int(_gsrc),
                'matched_pred_source': None if _ps is None else int(_ps)}
        if _ps is None:
            _rec['first_missing'] = 'no_matched_pred_source'
        else:
            _od = len(_pred_out.get(_ps, ()))
            _rec['pred_source_out_degree'] = int(_od)
            _js = _by_src.get(_ps, [])
            if _od >= 2:
                _rec['first_missing'] = 'already_pred_fork'   # division already present
            elif _od == 0:
                _rec['first_missing'] = 'pred_source_no_outgoing_edge'
            elif not _js:
                _rec['first_missing'] = 'source_never_reached_safe_div_candidate_loop'
            else:
                # furthest stage its best candidate reached; the "first missing" is the gate
                # immediately after that stage that blocked deployment.
                _best = max(_js, key=lambda c: _ORD.get(c['stage'], -1))
                _rec['best_candidate_furthest_stage'] = _best['stage']
                _rec['first_missing'] = ('recovered_added_final' if _best['stage'] == 'added_final'
                                         else 'blocked_at_' + _best['stage'])
        _coverage.append(_rec)
_dump_jsonl('exp058_gt_coverage.jsonl', _coverage)
_coverage_ok = (len(_coverage) == _GT_DIVISIONS_EXPECTED) and (_gt_div_total == _GT_DIVISIONS_EXPECTED)

# ---- 4) P3: fork relations (descriptive; only the aggregate 3/8/9 is official) ----
#          + downstream tracing of accepted safe_division edges (added_final vs final graph)
#          + one-at-a-time WHOLE-PANEL official-score suppression/addition deltas.
_forks = []
_suppression = []
_addition = []
_downstream = []
_base_panel = float(_official.get('proxy_score', float('nan')))


def _panel_delta(stem, new_row):
    # replace `stem`'s row with new_row, re-aggregate the whole 16-video panel officially
    _rr = [(_g2['row'] if _s2 != stem else new_row) for _s2, _g2 in _graphs.items()]
    _ag = aggregate_official(_rr)
    return _ag, (float(_ag['proxy_score']) - _base_panel)

for _stem, _g in _graphs.items():
    _pn, _pe, _gn, _ge = _g['pred_nodes'], _g['pred_edges'], _g['gt_nodes'], _g['gt_edges']
    _p2g, _g2p = match_nodes_bipartite(_pn, _gn, max_dist=VALIDATOR_MATCH_RADIUS_UM)
    _gt_out = _out_map(_ge)
    _pred_out = _out_map(_pe)
    _gt_div_srcs = {s for s, o in _gt_out.items() if len(o) >= 2}
    _pe_set = set(_pe)
    _sc = _cands_by_stem.get(_stem, [])
    _added = {(c['source_id'], c['candidate_id']) for c in _sc if c['stage'] == 'added_final'}
    _added_srcs = {s for s, _c in _added}
    # ambiguity: does any GT division source map (within radius) to >1 pred fork, or vice versa?
    _fork_nodes = [n for n, o in _pred_out.items() if len(o) >= 2]
    _gtdiv_to_forks = {}
    for _n in _fork_nodes:
        _mg = _p2g.get(_n)
        if _mg in _gt_div_srcs:
            _gtdiv_to_forks.setdefault(_mg, []).append(_n)
    _ambiguous = any(len(v) > 1 for v in _gtdiv_to_forks.values())
    for _n in _fork_nodes:
        _mg = _p2g.get(_n)
        _forks.append({'stem': _stem, 'fork': int(_n), 'out_degree': int(len(_pred_out[_n])),
            'matched_gt': None if _mg is None else int(_mg),
            'matched_gt_is_division_source': bool(_mg in _gt_div_srcs),
            'is_safe_division_added': bool(_n in _added_srcs),
            'matching_ambiguous_in_stem': bool(_ambiguous)})
    # downstream tracing: did each accepted safe_division edge survive to the final graph?
    for (_s, _c) in _added:
        _downstream.append({'stem': _stem, 'edge': [int(_s), int(_c)],
            'survived_to_final_graph': bool((_s, _c) in _pe_set)})
    # suppression: remove each surviving safe_division-added edge; WHOLE-PANEL official delta
    for (_s, _c) in _added:
        if (_s, _c) not in _pe_set:
            continue
        _ne = [e for e in _pe if not (e[0] == _s and e[1] == _c)]
        _nr = score_sample(_pn, _ne, _gn, _ge, _g['t_true'])
        _ag, _dp = _panel_delta(_stem, _nr)
        _suppression.append({'stem': _stem, 'edge': [int(_s), int(_c)],
            'd_div_tp': int(_ag['div_tp'] - _off_div[0]), 'd_div_fp': int(_ag['div_fp'] - _off_div[1]),
            'd_div_fn': int(_ag['div_fn'] - _off_div[2]), 'd_panel_proxy_score': float(_dp)})
    # addition population (defined): candidates that reached >= geometric_ok but were NOT
    # deployed (added_final). Add the (source, candidate) edge; WHOLE-PANEL official delta.
    _reached_geom = {}
    for _cc in _sc:
        if _ORD.get(_cc['stage'], -1) >= _ORD['geometric_ok']:
            _key = (_cc['source_id'], _cc['candidate_id'])
            _reached_geom.setdefault(_key, set()).add(_cc['stage'])
    for (_s, _c), _stages in _reached_geom.items():
        if (_s, _c) in _added or (_s, _c) in _pe_set:
            continue
        _ne = list(_pe) + [(_s, _c)]
        _nr = score_sample(_pn, _ne, _gn, _ge, _g['t_true'])
        _ag, _dp = _panel_delta(_stem, _nr)
        _addition.append({'stem': _stem, 'edge': [int(_s), int(_c)],
            'blocked_stages': sorted(_stages),
            'd_div_tp': int(_ag['div_tp'] - _off_div[0]), 'd_div_fp': int(_ag['div_fp'] - _off_div[1]),
            'd_div_fn': int(_ag['div_fn'] - _off_div[2]), 'd_panel_proxy_score': float(_dp)})
_dump_jsonl('exp058_fork_relations.jsonl', _forks)
_dump_jsonl('exp058_downstream_tracing.jsonl', _downstream)
_dump_jsonl('exp058_suppression.jsonl', _suppression)
_dump_jsonl('exp058_addition.jsonl', _addition)

# ---- 5) directionality: DeepCenter score vs source-maps-GT-division (p2g; join at cand_t) ----
_dc_by_key = {}
for _d in _dcs:
    if _d['prefix'] == 'safe_div' and _d['score'] is not None:
        _dc_by_key[(_d['dataset'], _d['t'], tuple(round(x, 4) for x in _d['point']))] = _d['score']
_direction = []
for _stem, _g in _graphs.items():
    _pn, _gn, _ge = _g['pred_nodes'], _g['gt_nodes'], _g['gt_edges']
    _p2g, _g2p = match_nodes_bipartite(_pn, _gn, max_dist=VALIDATOR_MATCH_RADIUS_UM)
    _gt_div_srcs = {s for s, o in _out_map(_ge).items() if len(o) >= 2}
    for _c in _cands_by_stem.get(_stem, []):
        if _c['stage'] != 'geometric_ok' or 'point' not in _c or 'cand_t' not in _c:
            continue
        _key = (_stem, int(_c['cand_t']), tuple(round(x, 4) for x in _c['point']))  # DeepCenter is at candidate time t+1
        _score = _dc_by_key.get(_key)
        _src_gt = _p2g.get(_c['source_id'])   # p2g: PRED source -> matched GT node
        _direction.append({'stem': _stem, 'source_id': int(_c['source_id']), 'candidate_id': int(_c['candidate_id']),
            'deepcenter_score': None if _score is None else float(_score),
            'source_maps_gt_division': bool(_src_gt in _gt_div_srcs)})
_dump_jsonl('exp058_directionality.jsonl', _direction)
_dc_join_rate = (sum(1 for d in _direction if d['deepcenter_score'] is not None) / len(_direction)) if _direction else 0.0

# ---- 6) effective-config capture (diagnostic-critical values, read from live globals) ----
def _gv(name):
    return _exp058_native(globals().get(name)) if '_exp058_native' in globals() else globals().get(name)
_effective_config = {k: _gv(k) for k in [
    'OUTPUT_SAFE_DIVISIONS', 'SAFE_DIV_MAX_UM', 'SAFE_DIV_SISTER_MAX_UM',
    'SAFE_DIV_EXISTING_CHILD_MAX_UM', 'SAFE_DIV_DIVERGE_UM', 'SAFE_DIV_SISTER_SYMMETRY_TAU',
    'SAFE_DIV_REQUIRE_MUTUAL_NN', 'SAFE_DIV_REQUIRE_DIVERGENCE',
    'SAFE_DIV_FRAME_FRAC_CAP', 'SAFE_DIV_GLOBAL_FRAC_CAP',
    'DEEPCENTER_SAFE_DIV_VETO', 'DEEPCENTER_SAFE_DIV_THRESHOLD', 'USE_DEEPCENTER_VETO',
    'VALIDATOR_MATCH_RADIUS_UM', 'VALIDATOR_DIVISION_WEIGHT', 'VALIDATOR_NODE_COUNT_PENALTY_A']}

# ---- 7) integrity gate + controller-valid metrics.json ----
def _json_native_ok(obj):
    try:
        _json.dumps(obj); return True
    except (TypeError, ValueError):
        return False

_runtime_s = float(_exp058_time.time() - _EXP058_T0)
_telemetry_complete = (len(_graphs) == 16) and (len(_cands) > 0) and _json_native_ok(_cands[:100]) \
    and _json_native_ok(_coverage) and _json_native_ok(_suppression) and _json_native_ok(_addition) \
    and _json_native_ok(_direction) and _json_native_ok(_forks) and _json_native_ok(_effective_config)
_checks = {
    'official_score_and_division_reproduced': bool(_official_ok),
    'test_submission_sha_matches_repro048': bool(_sha_ok),
    'sixteen_stems_present': bool(len(_graphs) == 16),
    'exactly_12_gt_divisions': bool(_coverage_ok),
    'telemetry_complete_native_json': bool(_telemetry_complete),
    'within_runtime_budget': bool(_runtime_s <= _RUNTIME_CEILING_S),
}
_integrity = all(_checks.values())

def _spec_metric(sp):
    _o = _spec_official.get(sp, {})
    return {'primary_metric': float(_o.get('proxy_score', float('nan'))),
            'adjusted_edge_jaccard': float(_o.get('adjusted_edge_jaccard', float('nan'))),
            'division_jaccard': float(_o.get('division_jaccard', float('nan'))),
            'division_tp': int(_o.get('div_tp', 0)), 'division_fp': int(_o.get('div_fp', 0)),
            'division_fn': int(_o.get('div_fn', 0))}

_metrics = {
    'schema_version': 1,
    'experiment_id': '__CONTROLLER_EXPERIMENT_ID__',
    'exp058_diagnostic_integrity_passed': bool(_integrity),
    'primary_metric': 1.0 if _integrity else 0.0,
    'primary_metric_meaning': 'binary_diagnostic_integrity: build-time purely-additive parity guard + runtime exact reproduction of official proxy 0.9310696 / division 3-8-9 / test submission SHA 0319ba6d. No quality or Public LB claim.',
    'runtime_seconds': _runtime_s,
    'reproducible': False,
    'specimen_metrics': {'44b6': _spec_metric('44b6'), '6bba': _spec_metric('6bba')},
    'checks': _checks,
    'official': {'proxy_score': float(_official.get('proxy_score', float('nan'))),
        'division_tp': _off_div[0], 'division_fp': _off_div[1], 'division_fn': _off_div[2],
        'adjusted_edge_jaccard': float(_official.get('adjusted_edge_jaccard', float('nan'))),
        'division_jaccard': float(_official.get('division_jaccard', float('nan')))},
    'expected': {'proxy_score': _EXP_SCORE, 'division': list(_EXP_DIV), 'submission_sha256': _EXP_SHA},
    'test_submission_sha256': _sub_sha,
    'effective_config': _effective_config,
    'counts': {'candidate_records': len(_cands), 'deepcenter_records': len(_dcs),
        'stems': len(_graphs), 'gt_divisions': _gt_div_total, 'gt_coverage_rows': len(_coverage),
        'forks': len(_forks), 'downstream_traced': len(_downstream),
        'suppression_edits': len(_suppression), 'addition_edits': len(_addition),
        'directionality_rows': len(_direction), 'directionality_dc_join_rate': _dc_join_rate},
    'validation': {'protocol': 'public_0944_train16_division_diagnostic_v1'},
    'note': 'DIAGNOSTIC ONLY. Official numbers come from the notebook inline scorer (match_nodes_bipartite / compute_division_confusion / score_sample / aggregate_official), not division_metrics. train16 is exhausted exploratory calibration; feature/direction separations are exploratory, not framework-selection evidence. No Public LB claim.',
}
with (_OUT / 'metrics.json').open('w', encoding='utf-8') as _f:
    _json.dump(_metrics, _f, indent=2)
print('exp058 integrity:', _integrity, _checks)
print('exp058 official proxy_score:', _official.get('proxy_score'), 'div:', _off_div, 'sub_sha ok:', _sha_ok,
      '| runtime_s:', round(_runtime_s, 1), '| gt_div rows:', len(_coverage))
'''

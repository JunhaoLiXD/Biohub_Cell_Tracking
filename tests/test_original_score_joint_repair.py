import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from scripts.original_score_joint_repair import DetectionProvenance, repair_graph


def make_cache(folder):
    ids = np.array([1, 2, 3, 4])
    coords = np.array([[0, 0, 0, 0], [0, 0, 0, 1], [1, 0, 0, 0], [1, 0, 0, 1]])
    np.savez(folder / 'pre_ilp_nodes.npz', graph_node_ids=ids, coords=coords)
    for frame in range(99):
        ij = np.array([[0, 0], [0, 1], [1, 0], [1, 1]]) if frame == 0 else np.empty((0, 2), dtype=int)
        np.savez(folder / f'pair_{frame:03d}_{frame+1:03d}.npz', pair_indices=ij,
                 source_ids=np.array([0, 1]), target_ids=np.array([2, 3]),
                 probabilities=np.array([.6, .85, .85, .6]) if frame == 0 else np.array([]),
                 threshold=np.array(.5))
    return ids, coords


def test_prediction_only_cache_repairs_occupied_slots_without_context(tmp_path):
    ids, coords = make_cache(tmp_path)
    nodes = {int(n): tuple(xyz) for n, xyz in zip(ids, coords)}
    before = nodes.copy()
    result, actions, _ = repair_graph(tmp_path, nodes, {(1, 3), (2, 4)}, set(ids))
    assert result == {(1, 4), (2, 3)}
    assert nodes == before and len(actions) == 1


def test_same_frame_recovered_id_cannot_inherit_provenance():
    nodes = {1: {'t': 0}, 2: {'t': 1}}
    p = DetectionProvenance([1, 2], [(0, 0, 0, 0), (1, 0, 0, 0)], nodes)
    nodes[1] = {'t': 0}
    assert p.observe(nodes) == {2}
    # Even restoring the original numeric ID/token cannot resurrect a removed identity.
    nodes[1]['_original_detection'] = (0, 0)
    assert p.observe(nodes) == {2}


def test_stage_removal_is_permanent_and_coordinate_smoothing_preserves_identity():
    nodes = {1: {'t': 0, 'x': 0}, 2: {'t': 1, 'x': 1}}
    p = DetectionProvenance([1, 2], [(0, 0, 0, 0), (1, 0, 0, 1)], nodes)
    nodes[2]['x'] = 1.25
    assert p.observe({2: nodes[2]}) == {2}
    assert p.observe(nodes) == {2}


def test_notebook_hooks_preserve_coordinates_and_write_prediction_receipt(tmp_path):
    from scripts import original_score_joint_repair as core
    folder = tmp_path / 'tracklet_evidence' / 'test_movie'
    folder.mkdir(parents=True)
    ids, coords = make_cache(folder)
    nodes = {int(n): dict(t=int(x[0]), z=float(x[1]), y=float(x[2]), x=float(x[3]))
             for n, x in zip(ids, coords)}
    edges = [dict(source_id=1, target_id=3), dict(source_id=2, target_id=4)]
    ns = dict(WORKING_DIR=tmp_path, np=np, json=json, _jr_module=core,
              edge_distance_um=lambda s, t: 1.)
    exec((Path(__file__).resolve().parents[1] / 'scripts/original_score_joint_hooks.py').read_text(), ns)
    ns['_jr_begin']('test_movie', nodes)
    ns['_jr_observe']('test_movie', nodes)
    before = {n: v.copy() for n, v in nodes.items()}
    result = ns['_jr_finish']('test_movie', nodes, edges)
    assert {(e['source_id'], e['target_id']) for e in result} == {(1, 4), (2, 3)}
    assert nodes == before
    assert (tmp_path / 'joint_repair/test_movie.json').is_file()

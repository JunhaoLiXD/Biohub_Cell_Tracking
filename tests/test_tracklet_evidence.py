"""Observation isolation, stable identity, sparse-pool semantics, strict serialization."""
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

ROOT = Path(__file__).resolve().parents[1]

def graph_hooks(tmp_path):
    namespace = dict(json=json, WORKING_DIR=tmp_path,
        _sha256_file=lambda p: hashlib.sha256(p.read_bytes()).hexdigest())
    exec((ROOT / 'scripts/tracklet_evidence_graphs.py').read_text(), namespace)
    return namespace

def test_disabled_graph_export_does_nothing(tmp_path):
    h = graph_hooks(tmp_path)
    h['_ev_graph']('movie', 'stage', {9: {'x': float('nan')}}, [])
    assert not list(tmp_path.iterdir())

def test_graph_order_identity_and_no_mutation(tmp_path):
    h = graph_hooks(tmp_path)
    h['EV_ENABLED'] = True
    nodes = {9: {'x': 1.25}, 3: {'x': 4.5}}
    edges = [{'source_id': 9, 'target_id': 3, 'edge_prob': None}]
    before = json.dumps([nodes, edges])
    h['_ev_graph']('movie', 'stage', nodes, edges)
    p = tmp_path / 'tracklet_evidence/movie/stage.json.gz'
    payload = json.loads(gzip.decompress(p.read_bytes()))
    assert [r[0] for r in payload['nodes']] == [9, 3]
    assert json.dumps([nodes, edges]) == before
    with pytest.raises(RuntimeError, match='Duplicate'):
        h['_ev_graph']('movie', 'stage', nodes, edges)

def test_nonfinite_graph_rejected(tmp_path):
    h = graph_hooks(tmp_path)
    h['EV_ENABLED'] = True
    with pytest.raises(ValueError):
        h['_ev_graph']('movie', 'stage', {9: {'x': float('nan')}}, [])

def test_worker_sparse_pool_and_inputs_unchanged(tmp_path):
    np = pytest.importorskip('numpy')
    import os
    h = dict(np=np, os=os, Path=Path)
    exec((ROOT / 'scripts/tracklet_evidence_worker.py').read_text(), h)
    h['_ev_stem'] = 'movie'
    h['_ev_cpu'] = lambda x: x.copy()
    captured = {}
    h['_ev_write'] = lambda name, arrays: captured.update(arrays)
    probs = np.arange(144, dtype=np.float32).reshape(12, 12) / 200
    src, tgt = np.arange(12), np.arange(12, 24)
    features = np.ones((1, 12, 33), np.float32)
    v = dict(probs=probs, idx_src=src, idx_tgt=tgt, all_edges=[(0, 12, 0., 1.)],
             cfg=SimpleNamespace(threshold=.3), secondary_logits_pair=probs[None],
             secondary_for_mix=probs[None], raw=probs, _ev_primary_logits=probs,
             c_src=np.zeros((12,4)), c_tgt=np.zeros((12,4)), ds_arr=np.ones(3),
             unet_feat_src=features, unet_feat_tgt=features,
             secondary_feat_src=features, secondary_feat_tgt=features,
             t_src=0, t_tgt=1, candidates=[(1,1,1)])
    old = probs.copy()
    h['_ev_pair'](v)
    ij = [tuple(p) for p in captured['pair_indices']]
    assert (0,0) in ij  # accepted edge outside top8 is retained
    assert captured['status'][ij.index((0,0))] == 2
    assert captured['status'][ij.index((0,11))] == 0
    assert captured['status'][ij.index((11,11))] == 1
    assert len(ij) < 144
    assert np.array_equal(probs, old)
    assert captured['primary_source_features'].shape == (12,33)
    assert captured['source_ids'].tolist() == src.tolist()

def test_worker_npz_roundtrip_and_nonfinite(tmp_path):
    np = pytest.importorskip('numpy')
    import os
    h = dict(np=np, os=os, Path=lambda p: tmp_path if str(p).startswith('/kaggle/') else Path(p))
    exec((ROOT / 'scripts/tracklet_evidence_worker.py').read_text(), h)
    h['_ev_stem'] = 'movie'
    values = np.asarray([[9, 3], [7, 8]], dtype=np.int64)
    h['_ev_write']('nodes', dict(ids=values))
    with np.load(tmp_path / 'movie/nodes.npz', allow_pickle=False) as data:
        assert np.array_equal(data['ids'], values)
    with pytest.raises(RuntimeError, match='Duplicate'):
        h['_ev_write']('nodes', dict(ids=values))
    with pytest.raises(ValueError, match='Nonfinite'):
        h['_ev_write']('bad', dict(values=np.asarray([float('inf')])))

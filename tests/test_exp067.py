"""Behavioral checks for the experimental temporal joint-lineage pipeline."""
import json
from dataclasses import replace
import numpy as np
import pytest
import torch

from scripts.exp067 import provenance as P, supervise as S, features as F
from scripts.exp067 import hypotheses as H, decode as D, runtime, train, checkpoint, infer
from scripts.exp067.config import Exp067Config


def fixture(stem='44b6_train'):
    ids = np.array([10, 20, 30, 40, 50, 60])
    times = np.array([0, 0, 1, 1, 2, 2])
    xyz = np.array([[0, 0, x] for x in [0, 10, 0, 10, 0, 10]], dtype=float)
    graph = P.FinalGraph(stem, ids, times, xyz, np.zeros(6, dtype=np.int8),
                         np.arange(6), np.array([10, 20, 30, 40]), np.array([30, 40, 50, 60]), {})
    emb = np.random.default_rng(9).normal(size=(6, 4)).astype('float32')
    pairs = [(s, t) for s in range(4) for t in range(6) if times[t] == times[s] + 1]
    ev = P.Evidence(stem, np.column_stack([times, xyz]), ids, emb, emb.copy(),
                    np.ones(6, bool), np.ones(6, bool), np.full(6, .8, 'float32'),
                    np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs]),
                    np.full(len(pairs), .5, 'float32'), np.zeros(len(pairs), 'float32'),
                    np.ones(len(pairs), dtype=np.int16), {'split': 'train',
                    'weights_sha256': {'fixture': 'synthetic-test-only'}, 'predict_source_sha256': 'fixture'})
    plain = {int(i): (int(t), *pos) for i, t, pos in zip(ids, times, xyz)}
    labels = S.build_label_set(stem, plain, plain, [(10, 30), (10, 40), (30, 50), (40, 60)], 1., 6)
    cfg = Exp067Config()
    cfg = replace(cfg, generation=replace(cfg.generation, event_require_geometry=False),
                  model=replace(cfg.model, d_model=8, n_layers=1),
                  train=replace(cfg.train, epochs=1, min_link_positives=1, min_division_positives=1))
    return graph, ev, labels, cfg


def program():
    graph, ev, _, cfg = fixture()
    hyp = H.generate(P.reconcile(graph, ev), cfg)
    _, ctx = F.build_batches(hyp, cfg)
    links = np.full(hyp.n_edges, -4.)
    desired = {(10, 30), (10, 40), (30, 50), (40, 60)}
    for k, (s, t) in enumerate(zip(hyp.e_src, hyp.e_tgt)):
        if (int(graph.node_id[s]), int(graph.node_id[t])) in desired:
            links[k] = 5.
    events = np.full(hyp.n_events, -10.)
    events[hyp.v_src == 0] = 8.
    return graph, cfg, D.build_program(hyp, ctx, links, events, cfg)


def test_joint_solver_reclaims_occupied_daughter():
    graph, cfg, prog = program()
    D.assert_parent_feasible(prog)
    assert all(len(D.component_transitions(prog, c)) == 1 for c in prog.components)
    result = D.solve(prog, cfg, runtime.Deadline(20), runtime.Receipt(dataset=graph.dataset, mode='decode'))
    selected = {(int(graph.node_id[s]), int(graph.node_id[t])) for s, t, keep in
                zip(prog.hyp.e_src, prog.hyp.e_tgt, result.selected_edges) if keep}
    assert selected == {(10, 30), (10, 40), (30, 50), (40, 60)}
    assert result.selected_events.sum() == 1


@pytest.mark.parametrize('failure', ['exception', 'invalid'])
def test_solver_failure_restores_parent(monkeypatch, failure):
    graph, cfg, prog = program()
    def broken(p, component, *args):
        if failure == 'exception':
            raise RuntimeError('simulated solver failure')
        return np.full(len(component), .3), None
    monkeypatch.setattr(D, '_solve_component', broken)
    result = D.solve(prog, cfg, runtime.Deadline(20), runtime.Receipt(dataset=graph.dataset, mode='decode'))
    np.testing.assert_array_equal(result.selected_edges, prog.parent_assignment[:prog.n_edge_vars] > .5)
    assert result.receipt.n_components_reverted > 0


def test_sparse_unknown_has_zero_gradient():
    _, _, labels, _ = fixture()
    assert S.link_label(labels, 10, 30) == 1
    assert S.link_label(labels, 10, 40) == 1
    assert S.link_label(labels, 999, 40) == -1
    assert S.division_label(labels, 10, 30, 40) == 1
    assert S.division_label(labels, 10, 40, 30) == 1
    logits = torch.zeros(3, requires_grad=True)
    train.masked_bce(logits, torch.tensor([1., 0., -1.]), torch.tensor([True, True, False])).backward()
    assert logits.grad[2] == 0
    assert logits.grad[0] < 0 < logits.grad[1]


def test_roundtrip_and_tamper(tmp_path):
    graph, ev, labels, _ = fixture()
    P.save_final_graph(tmp_path / 'g.npz', graph)
    P.save_evidence(tmp_path / 'e.npz', ev)
    S.save_label_set(tmp_path / 'l.npz', labels, labels.gt_nodes_plain)
    P.reconcile(P.load_final_graph(tmp_path / 'g.npz'), P.load_evidence(tmp_path / 'e.npz'))
    assert S.load_label_set(tmp_path / 'l.npz').gt_edges == labels.gt_edges
    with np.load(tmp_path / 'e.npz', allow_pickle=False) as z:
        arrays = {k: z[k] for k in z.files}
    arrays['emb_src'][0, 0] += 1
    np.savez_compressed(tmp_path / 'e.npz', **arrays)
    with pytest.raises(Exception, match='hash|SHA|sha'):
        P.load_evidence(tmp_path / 'e.npz')


def test_split_overlap_rejected(tmp_path):
    p = tmp_path / 'splits.json'
    p.write_text(json.dumps({'train': ['x_a'], 'holdout': ['x_a']}))
    with pytest.raises(Exception, match='both'):
        S.load_splits(p)


def test_parent_control_and_origins(monkeypatch):
    from scripts.exp067 import bridge
    graph, ev, _, cfg = fixture()
    result = infer.decode_graph(graph, ev, None, None, cfg, mode=runtime.MODE_PARENT)
    assert set(result.edges) == graph.parent_edge_set()
    monkeypatch.setenv('BIOHUB_EXP067_EXPORT', '0')
    monkeypatch.setenv('BIOHUB_EXP067_ENABLE', '0')
    nodes, edges = {}, []
    n, e = bridge.final_stage(nodes, edges, {}, 'unused')
    assert n is nodes and e is edges
    assert P.classify_origin({'_exp067_origin': 2}) == 2
    assert P.classify_origin({'gapfill_peak': 1}) == 1


def test_real_parent_patch_compiles():
    from scripts.exp067 import patching
    source = patching.replay_parent()
    patched = patching.patch_predictor(source)
    compile(patched, '<predictor>', 'exec')
    with pytest.raises(Exception):
        patching.patch_predictor(patched)
    for mode, kwargs in [('control', {}), ('export', {'stems': ['x_train', 'x_val']}),
                          ('decode', {'checkpoint': '/kaggle/input/model/model.pt'})]:
        nb = patching.patch_notebook(mode, **kwargs)
        for c in nb['cells']:
            if c['cell_type'] == 'code':
                compile(''.join(c['source']), '<notebook>', 'exec')


def test_cpu_train_save_load_decode(tmp_path):
    cfg = None
    for stem in ['44b6_train', '44b6_val']:
        graph, ev, labels, cfg = fixture(stem)
        P.save_final_graph(tmp_path / f'{stem}.final.npz', graph)
        P.save_evidence(tmp_path / f'{stem}.npz', ev)
        S.save_label_set(tmp_path / 'labels' / f'{stem}.npz', labels, labels.gt_nodes_plain)
    splits = tmp_path / 'splits.json'
    splits.write_text(json.dumps({'train': ['44b6_train'], 'holdout': ['44b6_val'], 'test_stems': []}))
    out = tmp_path / 'model.pt'
    report = train.train(tmp_path, tmp_path / 'labels', splits, out, cfg)
    assert report['division_head_trained']
    model, norm, metadata = checkpoint.load(out, emb_channels=4, config=cfg)
    checkpoint.validate_export(metadata, ev)
    with pytest.raises(Exception, match='configuration mismatch'):
        checkpoint.load(out, config=Exp067Config())
    result = infer.decode_graph(graph, ev, model, norm, cfg)
    assert result.receipt.n_components_solved > 0
    assert result.receipt.n_components_reverted == 0
    from scripts.exp067.evaluate import score_one
    score = score_one(graph, result.edges, labels)
    assert score is not None
    config_path = tmp_path / 'config.json'
    config_path.write_text(json.dumps(cfg.to_dict()))
    assert infer.main(['--export-dir', str(tmp_path), '--stems', '44b6_val', '--ckpt', str(out),
                       '--config', str(config_path), '--out', str(tmp_path / 'decoded')]) == 0
    from scripts.exp067 import evaluate
    assert evaluate.main(['--export-dir', str(tmp_path), '--label-dir', str(tmp_path / 'labels'),
                          '--stems', '44b6_val', '--decoded-dir', str(tmp_path / 'decoded'),
                          '--out', str(tmp_path / 'comparison.json')]) == 0


def test_division_head_is_symmetric_and_trainable():
    from scripts.exp067.model import JointLineageScorer
    _, _, _, cfg = fixture()
    model = JointLineageScorer(4, cfg.model)
    hidden = torch.randn(1, 3, cfg.model.d_model)
    ef = torch.randn(1, F.N_EVENT_FEATURES)
    a = model.score_events(hidden, torch.tensor([[0, 1, 2]]), ef)
    b = model.score_events(hidden, torch.tensor([[0, 2, 1]]), ef)
    torch.testing.assert_close(a, b, rtol=0, atol=0)
    a.sum().backward()
    assert sum(p.grad.abs().sum().item() for p in model.division_head.parameters()) > 0


def test_required_endpoints_split_and_overflow():
    from scripts.exp067.errors import Exp067WindowOverflow
    graph, ev, _, cfg = fixture()
    hyp = H.generate(P.reconcile(graph, ev), cfg)
    ctx = F.build_movie_context(hyp)
    plans = F.plan_batches(hyp, ctx, replace(cfg.window, required_cap=3))
    assert len(plans) == 4
    assert all(len(p['rows']) == 3 for p in plans)
    with pytest.raises(Exp067WindowOverflow):
        F.plan_batches(hyp, ctx, replace(cfg.window, required_cap=2))


def test_parent_fork_and_fixed_boundary_remain_feasible():
    graph, ev, _, cfg = fixture()
    graph.edge_src = np.array([10, 10, 30, 40])
    graph.edge_tgt = np.array([30, 40, 50, 60])
    graph.node_origin[3] = 2
    graph.node_det_row[3] = -1
    hyp = H.generate(P.reconcile(graph, ev), cfg)
    _, ctx = F.build_batches(hyp, cfg)
    prog = D.build_program(hyp, ctx, np.full(hyp.n_edges, -5.), np.full(hyp.n_events, -5.), cfg)
    D.assert_parent_feasible(prog)
    result = D.solve(prog, cfg, runtime.Deadline(20), runtime.Receipt(graph.dataset, 'decode'))
    assert result.selected_edges[hyp.e_fixed].all()


def test_measured_feature_hook_and_fatal_propagation(tmp_path, monkeypatch):
    from pathlib import Path
    from scripts.exp067 import bridge, export_hooks as hooks
    class Model:
        def _index_features(self, feat, coords, mask):
            return torch.ones(1, coords.shape[1], feat.shape[1]) * 3
    hooks.begin_video('sample')
    bridge.first_seen({'ds_path': Path('sample.zarr'), 'arr': np.array([[0, 1, 1, 1]]),
                      'global_node_count': 0, 'f_idx': 0, 'model': Model(),
                      'unet_out': torch.ones(1, 2, 4, 3, 3, 3),
                      'det_logits': [torch.zeros(1, 1, 3, 3, 3)] * 2})
    buf = hooks.buffer_for('sample')
    assert buf.det_score[0] == .5
    np.testing.assert_array_equal(buf.emb_src[0], np.full(4, 3))
    monkeypatch.setenv('BIOHUB_EXP067_EXPORT', '1')
    monkeypatch.setenv('BIOHUB_EXP067_EXPORT_DIR', str(tmp_path))
    runtime.clear_fatal()
    with pytest.raises(Exception):
        bridge.tag_original({}, 'missing')
    with pytest.raises(RuntimeError, match='EXP067 FATAL'):
        runtime.raise_if_fatal()
    runtime.clear_fatal()


def test_parent_scorer_is_verbatim():
    from scripts.exp067 import extract_parent_scorer as E, parent_scorer
    from scripts.exp067.patching import PARENT
    import inspect
    original = E.extract(E.read_cell(PARENT, 8), E.FUNCTIONS)
    for name, source in original.items():
        assert inspect.getsource(getattr(parent_scorer, name)).strip() == source.strip()

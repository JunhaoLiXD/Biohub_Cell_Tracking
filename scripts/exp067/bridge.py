"""Measured predictor hooks and final-graph integration; no labels in decode paths."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import numpy as np

from . import export_hooks as hooks, provenance, runtime


def enabled():
    return runtime.env_flag(runtime.ENV_EXPORT) or runtime.env_flag(runtime.ENV_ENABLE)


def first_seen(v):
    """Sample actual fused detector confidence and frozen features, never substitute scores."""
    import torch
    stem = v['ds_path'].stem
    arr = v['arr']
    indices = np.arange(v['global_node_count'], v['global_node_count'] + len(arr))
    if not len(arr):
        return
    feat = v['unet_out'][:, v['f_idx']]
    coords = torch.as_tensor(arr[:, 1:].copy(), dtype=torch.float32, device=feat.device)[None]
    mask = torch.ones((1, len(arr)), dtype=torch.bool, device=feat.device)
    measured = v['model']._index_features(feat, coords, mask).detach().float().cpu().numpy()
    role = 'src' if v['f_idx'] == 0 else 'tgt'
    hooks.record_embeddings(stem, role, indices, measured)
    # The refined coordinate is measured against the actual fused detection heatmap.
    logits = v['det_logits'][v['f_idx']].reshape(*feat.shape[-3:])
    q = coords[0].round().long()
    for axis, size in enumerate(logits.shape):
        q[:, axis].clamp_(0, size - 1)
    scores = torch.sigmoid(logits[q[:, 0], q[:, 1], q[:, 2]])
    hooks.record_detection(stem, indices, scores.detach().float().cpu().numpy())


def pair(v):
    stem = v['ds_path'].stem
    hooks.record_alternatives(stem, v['idx_src'], v['idx_tgt'], v['probs'],
                              v['raw'].detach().float().cpu().numpy())
    for role in ('src', 'tgt'):
        hooks.record_embeddings(stem, role, v['idx_' + role],
                                v['unet_feat_' + role].detach().float().cpu().numpy())


def finish_predictor(v):
    paths = {'primary': str(v['weights_path']),
             'secondary': os.environ.get('BIOHUB_SECONDARY_WEIGHTS', ''),
             'coordinate_head': os.environ.get('V1284_HEAD', '')}
    hashes = {}
    for key, value in paths.items():
        if not value or not Path(value).is_file():
            raise ValueError(f'exp067 missing required {key} checkpoint')
        hashes[key] = hashlib.sha256(Path(value).read_bytes()).hexdigest()
    stem = Path(v['name']).stem
    hooks.write_video_export(stem, v['coords'], manifest_extras={
        'weights_sha256': hashes, 'split': os.environ.get('BIOHUB_EXP067_SPLIT', 'test'),
        'predict_source_sha256': hashlib.sha256(Path(v['__file__']).read_bytes()).hexdigest(),
        'downsample': list(v['downsample']), 'window_size': int(v['window_size']),
    })


def tag_original(nodes, stem):
    if not enabled():
        return
    try:
        _tag_original(nodes, stem)
    except Exception as exc:
        runtime.set_fatal(f'{stem}: original identity export failed: {exc}')
        raise


def _tag_original(nodes, stem):
    evidence = provenance.load_evidence(hooks.export_dir() / f'{stem}.npz')
    for node_id, node in nodes.items():
        row = evidence.row_of_node_id.get(int(node_id))
        actual = np.array([node['t'], node['z'], node['y'], node['x']], dtype=float)
        if row is None or not np.allclose(actual, evidence.coords[row], atol=1e-5, rtol=0):
            raise ValueError(f'exp067 original identity/coordinate mismatch: {stem}:{node_id}')
        node['_exp067_det_row'] = row


def final_stage(nodes, edges, stats, stem):
    if not enabled():
        return nodes, edges
    try:
        mapping = {int(k): int(v['_exp067_det_row']) for k, v in nodes.items()
                   if '_exp067_det_row' in v and provenance.classify_origin(v) == 0}
        for k, node in nodes.items():
            if provenance.classify_origin(node) == 0 and k not in mapping:
                raise ValueError(f'exp067 untracked/reused original identity {stem}:{k}')
        evidence = provenance.load_evidence(hooks.export_dir() / f'{stem}.npz')
        graph = provenance.final_graph_from_parent(stem, nodes, edges, mapping)
        provenance.reconcile(graph, evidence)
        hooks.write_final_graph(stem, nodes, edges, mapping,
                                split=os.environ.get('BIOHUB_EXP067_SPLIT', 'test'))
        if runtime.env_flag(runtime.ENV_ENABLE):
            from .infer import joint_reconsider
            return joint_reconsider(nodes, edges, stats, stem, det_row_of_node=mapping)
        return nodes, edges
    except Exception as exc:
        runtime.set_fatal(f'{stem}: {type(exc).__name__}: {exc}')
        return nodes, edges


def label_stage(stem, nodes, gt_nodes, gt_edges, t_true):
    if not runtime.env_flag(runtime.ENV_LABELS):
        return
    selected = set(os.environ[runtime.ENV_LABEL_STEMS].split(','))
    if stem not in selected or os.environ.get('BIOHUB_EXP067_SPLIT') != 'train':
        raise ValueError('label export outside explicit TRAIN manifest')
    from .export_hooks import write_labels
    write_labels(stem, nodes, gt_nodes, gt_edges, 7.0, t_true,
                 hooks.export_dir() / 'labels')

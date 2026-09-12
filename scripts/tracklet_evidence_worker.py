"""Read-only worker hooks, embedded in the frozen predictor by the builder.

No labels, randomness, model calls, or writes to predictor arrays are used.
Sparse candidate pool: top eight per source and target plus every accepted edge.
Unexported pairs remain unmeasured, not classified as unreachable.
"""
import gzip as _ev_gzip
import hashlib as _ev_hash

_ev_stem = None

def _ev_begin(path):
    global _ev_stem
    _ev_stem = Path(path).stem if os.environ.get("BIOHUB_TRACKLET_EVIDENCE") == "validation" else None

def _ev_write(name, arrays):
    if _ev_stem is None:
        return
    for value in arrays.values():
        if value.dtype.kind == "f" and not np.isfinite(value).all():
            raise ValueError("Nonfinite evidence: " + name)
    folder = Path('/kaggle/working/tracklet_evidence') / _ev_stem
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (name + '.npz')
    if path.exists():
        raise RuntimeError('Duplicate evidence: ' + str(path))
    np.savez_compressed(path, **arrays)
    # Per-video cap: bounded to 128 MiB, at most 2 GiB over frozen train16.
    total = sum(p.stat().st_size for p in folder.glob('*.npz'))
    if total > 128 * 1024**2:
        raise RuntimeError('Evidence budget exceeded: ' + _ev_stem)

def _ev_cpu(tensor):
    return tensor.detach().float().cpu().numpy().copy()

def _ev_primary(tensor):
    return _ev_cpu(tensor[0]) if _ev_stem is not None else None

def _ev_pair(v):
    if _ev_stem is None:
        return
    probs = v['probs']
    ns, nt = probs.shape
    # Stable sorting affects only the observation pool, never inference.
    pool = {(i, int(j)) for i in range(ns)
            for j in np.argsort(-probs[i], kind='stable')[:8]}
    pool.update((int(i), j) for j in range(nt)
                for i in np.argsort(-probs[:, j], kind='stable')[:8])
    src_index = {int(n): i for i, n in enumerate(v['idx_src'])}
    tgt_index = {int(n): j for j, n in enumerate(v['idx_tgt'])}
    accepted = {(src_index[s], tgt_index[t]) for s, t, _, _ in v['all_edges']
                if s in src_index and t in tgt_index}
    pool.update(accepted)
    ij = np.asarray(sorted(pool), dtype=np.int64).reshape(-1, 2)
    i, j = ij[:, 0], ij[:, 1]
    # Status 0=below/equal threshold, 1=above threshold rejected by degree caps,
    # 2=accepted before ILP. Every accepted pair is present; this is NOT all pairs.
    status = np.asarray([2 if (a, b) in accepted else
                         1 if probs[a, b] > v['cfg'].threshold else 0
                         for a, b in ij], dtype=np.int8)
    secondary = _ev_cpu(v['secondary_logits_pair'][0])
    secondary_aligned = _ev_cpu(v['secondary_for_mix'][0])
    final = _ev_cpu(v['raw'])
    arrays = dict(
        pair_indices=ij, source_ids=v['idx_src'], target_ids=v['idx_tgt'],
        source_coords_downsampled=v['c_src'], target_coords_downsampled=v['c_tgt'],
        downsample=v['ds_arr'], primary_logits=v['_ev_primary_logits'][i, j],
        secondary_logits=secondary[i, j], secondary_aligned_logits=secondary_aligned[i, j],
        blended_logits=final[i, j], probabilities=probs[i, j], status=status,
        primary_source_features=_ev_cpu(v['unet_feat_src'][0]),
        primary_target_features=_ev_cpu(v['unet_feat_tgt'][0]),
        secondary_source_features=_ev_cpu(v['secondary_feat_src'][0]),
        secondary_target_features=_ev_cpu(v['secondary_feat_tgt'][0]),
        frame_pair=np.asarray([v['t_src'], v['t_tgt']], dtype=np.int64),
        threshold=np.asarray(v['cfg'].threshold),
        full_pair_count=np.asarray(ns * nt),
        above_threshold_count=np.asarray(len(v['candidates'])),
        accepted_count=np.asarray(len(accepted)),
    )
    _ev_write('pair_%03d_%03d' % (v['t_src'], v['t_tgt']), arrays)

def _ev_nodes(coords, node_ids):
    if _ev_stem is not None:
        _ev_write('pre_ilp_nodes', dict(coords=coords.copy(),
                  graph_node_ids=np.asarray(node_ids, dtype=np.int64),
                  detection_ids=np.arange(len(coords), dtype=np.int64)))

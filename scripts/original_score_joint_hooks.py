"""Notebook prediction hooks, shared by test and validation."""
import hashlib
JR_PROVENANCE = {}
JR_RECEIPTS = {}


def _jr_begin(stem, nodes):
    folder = WORKING_DIR / 'tracklet_evidence' / stem
    with np.load(folder / 'pre_ilp_nodes.npz', allow_pickle=False) as reg:
        JR_PROVENANCE[stem] = _jr_module.DetectionProvenance(
            reg['graph_node_ids'], reg['coords'], nodes)


def _jr_observe(stem, nodes):
    if stem in JR_PROVENANCE:
        JR_PROVENANCE[stem].observe(nodes)


def _jr_hash(nodes, edges):
    payload = dict(pred_nodes=sorted(nodes.items()), pred_edges=sorted(edges))
    return hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()


def _jr_finish(stem, nodes, edges):
    plain = {n: (int(v['t']), float(v['z']), float(v['y']), float(v['x']))
             for n, v in nodes.items()}
    old = {(int(e['source_id']), int(e['target_id'])) for e in edges}
    persistent = JR_PROVENANCE[stem].observe(nodes)
    edited, actions, coverage = _jr_module.repair_graph(
        WORKING_DIR / 'tracklet_evidence' / stem, plain, old, persistent)
    existing = {(int(e['source_id']), int(e['target_id'])): e for e in edges}
    result = []
    for s, t in sorted(edited):
        if (s, t) in existing:
            result.append(existing[s, t])
        else:
            result.append(dict(source_id=s, target_id=t,
                               distance_um=edge_distance_um(nodes[s], nodes[t])))
    receipt = dict(input_graph_sha256=_jr_hash(plain, old),
                   output_graph_sha256=_jr_hash(plain, edited),
                   actions=actions, coverage=coverage, persistent_nodes=len(persistent))
    if stem in JR_RECEIPTS:
        raise RuntimeError('Duplicate joint repair execution: ' + stem)
    JR_RECEIPTS[stem] = receipt
    folder = WORKING_DIR / 'joint_repair'
    folder.mkdir(exist_ok=True)
    (folder / (stem + '.json')).write_text(json.dumps(receipt, allow_nan=False))
    del JR_PROVENANCE[stem]
    return result

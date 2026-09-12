"""Notebook observation hooks. IDs and insertion order are preserved."""
import gzip as _ev_graph_gzip

EV_ENABLED = False
EV_MANIFEST = {}

def _ev_json_default(value):
    if hasattr(value, 'item'):
        return value.item()
    raise TypeError(type(value).__name__)

def _ev_json(stem, stage, payload):
    if not EV_ENABLED:
        return
    raw = json.dumps(payload, allow_nan=False, default=_ev_json_default).encode('utf-8')
    path = WORKING_DIR / 'tracklet_evidence' / stem / (stage + '.json.gz')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeError('Duplicate graph stage: ' + str(path))
    path.write_bytes(_ev_graph_gzip.compress(raw, mtime=0))
    EV_MANIFEST.setdefault(stem, {})[stage] = dict(path=str(path), sha256=_sha256_file(path))

def _ev_graph(stem, stage, nodes, edges):
    if EV_ENABLED:
        _ev_json(stem, stage, dict(stage=stage, nodes=list(nodes.items()), edges=edges))

def _ev_final(stem, pn, pe, gn, ge, t_true, row):
    _ev_json(stem, 'final_scored', dict(pred_nodes=list(pn.items()), pred_edges=pe,
             gt_nodes=list(gn.items()), gt_edges=ge, t_true=t_true, score_row=row))

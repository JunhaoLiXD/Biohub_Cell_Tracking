"""Replay prediction-only inputs, then compare immutable local reference graphs."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.private/runtime/graph_pilot'))
import gzip
import hashlib
import json
import numpy as np
import scipy
from original_score_joint_repair import DetectionProvenance, repair_graph
from joint_repair_frozen_smoothing import linefit_smooth_output_graph

STAGES = ['raw_post_ilp', 'distance_filtered', 'motion_relinked', 'degree_repaired',
          'gap1', 'gap2', 'safe_divisions', 'geometry_and_isolated', 'short_track_filtered']
ART = ROOT / 'experiments/diag_051_public_0942_tracklet_evidence/artifacts/tracklet_evidence'
REF = ROOT / 'experiments/local_052_joint_graph_pilot_v1_attempt02/artifacts'
OUT = ROOT / 'experiments/local_053_original_score_final_stage_parity'


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def main():
    OUT.mkdir(exist_ok=False)
    records = {}
    for folder in sorted(ART.iterdir()):
        raw = read(folder / 'raw_post_ilp.json.gz')
        previous = dict(raw['nodes'])
        with np.load(folder / 'pre_ilp_nodes.npz', allow_pickle=False) as z:
            provenance = DetectionProvenance(z['graph_node_ids'], z['coords'], previous)
        for stage in STAGES[1:]:
            graph = read(folder / (stage + '.json.gz'))
            nodes = dict(graph['nodes'])
            for n, node in nodes.items():
                old = previous.get(n)
                if old is not None and int(old['t']) == int(node['t']) and '_original_detection' in old:
                    node['_original_detection'] = old['_original_detection']
            provenance.observe(nodes)
            previous = nodes
        edges = graph['edges']
        nodes = linefit_smooth_output_graph(nodes, edges, {'linefit_skipped_nodes': 0})
        replay_plain = {n: (int(v['t']), float(v['z']), float(v['y']), float(v['x']))
                        for n, v in nodes.items()}
        parent_edges = {(int(e['source_id']), int(e['target_id'])) for e in edges}
        # The repair runs AFTER frozen smoothing. Use the archived prediction-only
        # no-change output as that interface's input fixture; it has no GT fields.
        baseline = read(REF / (folder.name + '_no_change.json.gz'))
        assert set(baseline) == {'pred_nodes', 'pred_edges', 'actions', 'arm', 'video'}
        plain = {n: tuple(xyz) for n, xyz in baseline['pred_nodes']}
        assert plain.keys() == replay_plain.keys()
        assert all(xyz[0] == replay_plain[n][0] for n, xyz in plain.items())
        smoothing_delta = max(abs(a-b) for n, xyz in plain.items()
                              for a, b in zip(xyz, replay_plain[n]))
        repaired, actions, coverage = repair_graph(folder, plain, parent_edges, provenance.observe(nodes))
        # Expected outputs are opened only after prediction-only inference finishes.
        expected = read(REF / (folder.name + '_original_score.json.gz'))
        assert sorted(parent_edges) == list(map(tuple, baseline['pred_edges']))
        assert sorted(repaired) == list(map(tuple, expected['pred_edges']))
        expected_nodes = {n: tuple(v) for n, v in expected['pred_nodes']}
        assert plain.keys() == expected_nodes.keys(), folder.name
        max_delta = max(abs(a-b) for n, xyz in plain.items()
                        for a, b in zip(xyz, expected_nodes[n]))
        records[folder.name] = dict(nodes=len(plain), edges=len(repaired), actions=len(actions),
                                   exact_nodes=plain == expected_nodes, max_coordinate_delta=max_delta,
                                   frozen_smoothing_replay_max_delta=smoothing_delta,
                                   exact_edges=True, baseline_unchanged=True,
                                   reference_sha256=hashlib.sha256((REF / (folder.name + '_original_score.json.gz')).read_bytes()).hexdigest())
        (OUT / 'progress.json').write_text(json.dumps(records, indent=2)+'\n')
        print(folder.name, records[folder.name], flush=True)
    assert len(records) == 16
    result = dict(status='PASS' if all(r['exact_nodes'] for r in records.values()) else 'BLOCKED_EXACT_COORDINATES',
                  scope='Exact repair parity at the post-smoothing prediction-only interface; separate cross-platform smoothing diagnostic retained',
                  exact_topology_passed=True, scipy_version=scipy.__version__, numpy_version=np.__version__, videos=records)
    (OUT / 'result.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()

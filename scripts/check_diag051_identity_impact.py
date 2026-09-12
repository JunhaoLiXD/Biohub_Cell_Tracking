"""Measure impact of recovered-ID collisions on the old residual diagnostic."""
from collections import Counter
import json
from pathlib import Path
import numpy as np
from diag051_offline_feasibility import extract_candidate_records, rank_stats
from diag052_joint_policy import STAGES, persistent_original_ids
from analyze_diag051_evidence import ART, read_graph

ROOT = Path(__file__).resolve().parents[1]


def main():
    metrics = json.loads((ART/'metrics.json').read_text())['metrics']
    ranks = {key: Counter() for key in ['probability','blended','primary_cosine','secondary_cosine']}
    videos = {}
    for stem in sorted(metrics['evidence_graph_manifest']):
        folder = ART/'tracklet_evidence'/stem
        f = read_graph(folder/'final_scored.json.gz')
        m = read_graph(folder/'scorer_matching.json.gz')
        pn, p2g, g2p = dict(f['pred_nodes']), dict(m['p2g']), dict(m['g2p'])
        pe = set(map(tuple,f['pred_edges']))
        mapped_gt = {(g2p[s],g2p[t]) for s,t in f['gt_edges'] if s in g2p and t in g2p}
        missing = mapped_gt-pe
        with np.load(folder/'pre_ilp_nodes.npz') as reg:
            ids,coords = reg['graph_node_ids'],reg['coords']
        valid = persistent_original_ids(ids,coords,pn,[dict(read_graph(folder/(s+'.json.gz'))['nodes']) for s in STAGES])
        records = []
        for t in range(99):
            with np.load(folder/f'pair_{t:03d}_{t+1:03d}.npz') as pair:
                records.extend(extract_candidate_records(pair,ids,{s for s,t in missing},mapped_gt,missing,valid,p2g))
        for name in ranks:
            values = rank_stats(records,name)
            ranks[name].update({k:values[k] for k in ['n','top1','top3','top8']})
        videos[stem] = {'candidate_rows':len(records),'residuals':sum(r['positive'] for r in records),
                        'accepted':sum(r['positive'] and r['status']==2 for r in records),
                        'rejected_final_ids':sorted((set(map(int,ids)) & pn.keys())-valid)}
    result = {'protocol':'residual_conditioned_identity_checked_v3',
              'ranking_summary':{k:dict(v) for k,v in ranks.items()},'videos':videos,
              'candidate_rows':sum(v['candidate_rows'] for v in videos.values()),
              'residuals':sum(v['residuals'] for v in videos.values()),
              'accepted':sum(v['accepted'] for v in videos.values()),
              'limitations':['Residual-conditioned recall, not deployment precision or heldout evaluation.',
                             'Reject nonpersistent or frame-mismatched reused node IDs.']}
    path = ROOT/'.private/research/diag051_audit/offline_feasibility_v3_identity_checked.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='videos'},indent=2))


if __name__ == '__main__':
    main()

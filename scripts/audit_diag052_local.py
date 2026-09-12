"""Independent output reconstruction and frozen-score audit; no policy rerun."""
from collections import Counter
import json
from pathlib import Path

from analyze_diag051_evidence import ART, F, read_graph, score, aggregate, sha

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT/'experiments/local_052_joint_graph_pilot_v1_attempt02'


def main():
    results = json.loads((RUN/'result.json').read_text())
    rows = {a: [] for a in ['no_change', 'original_score', 'context']}
    counts = {a: Counter() for a in rows}
    for stem, video in results['videos'].items():
        parent = read_graph(ART/'tracklet_evidence'/stem/'final_scored.json.gz')
        matching = read_graph(ART/'tracklet_evidence'/stem/'scorer_matching.json.gz')
        pn, gn = dict(parent['pred_nodes']), dict(parent['gt_nodes'])
        pe, ge = set(map(tuple, parent['pred_edges'])), set(map(tuple, parent['gt_edges']))
        p2g, g2p = dict(matching['p2g']), dict(matching['g2p'])
        for arm, expected in video['arms'].items():
            path = RUN/'artifacts'/f'{stem}_{arm}.json.gz'
            assert sha(path) == expected['graph_sha256']
            artifact = read_graph(path)
            assert dict(artifact['pred_nodes']) == pn
            edited = set(map(tuple, artifact['pred_edges']))
            assert len(edited) == len(artifact['pred_edges'])
            assert max(Counter(s for s, t in edited).values(), default=0) <= 2
            assert max(Counter(t for s, t in edited).values(), default=0) <= 1
            assert all(pn[t][0] == pn[s][0]+1 for s, t in edited)
            reconstructed = set(pe)
            all_added, all_removed = set(), set()
            for action in artifact['actions']:
                adds, removes = set(map(tuple, action['added'])), set(map(tuple, action['removed']))
                assert adds and action['objective_gain'] > 0
                assert removes <= reconstructed and not adds & reconstructed
                assert not all_added & adds and not all_removed & removes
                all_added |= adds
                all_removed |= removes
                reconstructed.difference_update(removes)
                reconstructed.update(adds)
            assert reconstructed == edited
            assert all_added == edited-pe and all_removed == pe-edited
            for name, changed in [('added', all_added), ('removed', all_removed)]:
                tp, fp, _ = F['compute_edge_confusion'](changed, ge, p2g, g2p)
                assert expected[name] == {'true': tp, 'false': fp, 'unknown': len(changed)-tp-fp}
            old_forks = {s for s, count in Counter(s for s, t in pe).items() if count == 2}
            new_forks = {s for s, count in Counter(s for s, t in edited).items() if count == 2}
            assert old_forks == new_forks
            assert {(s,t) for s,t in pe if s in old_forks} == {(s,t) for s,t in edited if s in old_forks}
            actual = score(pn, edited, gn, ge, p2g, g2p, parent['t_true'])
            for key, value in actual.items():
                assert abs(value-expected['score'][key]) < 1e-12
            rows[arm].append(actual)
            for label in ['true', 'false', 'unknown']:
                counts[arm]['added_'+label] += expected['added'][label]
                counts[arm]['removed_'+label] += expected['removed'][label]
            counts[arm]['added'] += len(all_added)
            counts[arm]['removed'] += len(all_removed)
            counts[arm]['actions'] += len(artifact['actions'])
            if arm == 'no_change':
                assert edited == pe
    for arm, scores in rows.items():
        for key, value in aggregate(scores).items():
            assert abs(value-results['summary']['all'][arm][key]) < 1e-12
    result = {'status': 'PASS', 'graphs_audited': sum(map(len, rows.values())),
              'checks': ['graph hashes', 'exact node preservation', 'action reconstruction',
                         'forward edges and degrees', 'fork identity', 'frozen edit labels',
                         'frozen full-graph scores', 'aggregate scores'],
              'edit_totals': {a: dict(c) for a,c in counts.items()},
              'result_sha256': sha(RUN/'result.json')}
    (RUN/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()

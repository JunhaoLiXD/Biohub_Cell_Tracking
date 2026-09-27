"""TRAIN-only, GT-assisted bounded counterfactual; never a deployable prediction policy."""
import csv
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.exp067 import provenance, supervise
from scripts.exp067.audit import audit_graph
from scripts.exp067.evaluate import score_one
from scripts.exp067.parent_scorer import aggregate_official

EXPORT = ROOT / '.private/runtime/exp067d_out/exp067_export'
OUT = ROOT / 'docs/research/ep015_continuation_2026-09-26/division_counterfactual.json'


def repaired_edges(parent, selected):
    requested = {(e['mother'], d) for e in selected for d in e['daughters']}
    sources = {e['mother'] for e in selected}
    targets = {b for _, b in requested}
    if len(targets) != len(requested):
        raise ValueError('Selected events request multiple parents for one daughter')
    retained = {edge for edge in parent if edge[0] not in sources and edge[1] not in targets}
    return retained | requested


def main():
    assert not OUT.exists(), 'Preserve prior diagnostic; use a new version to rerun'
    q1 = json.loads((ROOT / 'docs/research/exp067_stage0_q1_headroom.json').read_text())
    originals = {r['stem']: r for r in csv.DictReader((EXPORT.parent / 'validator_results.csv').open()) if r['config'] == 'base'}
    events, by_stem, baseline, hashes = [], {}, {}, {}
    for item in q1['per_stem']:
        stem = item['stem']
        graph_path, label_path = EXPORT / f'{stem}.final.npz', EXPORT / 'labels' / f'{stem}.npz'
        assert not stem in ('44b6_0113de3b','44b6_0b24845f','6bba_05b6850b','6bba_05db0fb1')
        graph, labels = provenance.load_final_graph(graph_path), supervise.load_label_set(label_path)
        for p in (graph_path, label_path):
            hashes[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
        parent = graph.parent_edge_set()
        base = score_one(graph, sorted(parent), labels)
        for k, value in base.items():
            if k in originals[stem] and isinstance(value, (int, float)) and originals[stem][k] != '':
                assert math.isclose(value, float(originals[stem][k]), rel_tol=0, abs_tol=1e-12), (stem, k, value, originals[stem][k])
        baseline[stem] = base
        reverse = {g: p for p, g in labels.pred_to_gt.items()}
        found = []
        for mother, children in sorted(labels.gt_children.items()):
            if len(children) < 2:
                continue
            daughters = sorted(children)[:2]
            if mother not in reverse or any(d not in reverse for d in daughters):
                continue
            pm, pd = reverse[mother], [reverse[d] for d in daughters]
            if all((pm, d) in parent for d in pd):
                continue
            event = {'index': len(events), 'stem': stem, 'gt_mother': mother, 'mother': pm, 'daughters': pd}
            events.append(event); found.append(event)
        expected = {r['gt_mother'] for r in item['rows'] if r['matched'] and not r['in_parent']}
        assert {e['gt_mother'] for e in found} == expected, 'Re-derived deficits differ from Q1'
        by_stem[stem] = (graph, labels, parent, found)
    assert len(events) == 7 and len(baseline) == 8
    base_aggregate = aggregate_official(list(baseline.values()))
    assert [base_aggregate[k] for k in ('div_tp','div_fp','div_fn')] == [3,2,9]
    cache, cases = {}, []
    for stem, (graph, labels, parent, local) in by_stem.items():
        node_t = dict(zip(map(int, graph.node_id), map(int, graph.node_t)))
        for bits in itertools.product((False, True), repeat=len(local)):
            selected = [e for e, yes in zip(local, bits) if yes]
            key = tuple(e['index'] for e in selected)
            edges = repaired_edges(parent, selected)
            audit_graph(node_t, sorted(edges))
            row = baseline[stem] if not selected else score_one(graph, sorted(edges), labels)
            removed, added = sorted(parent - edges), sorted(edges - parent)
            true_removed = [e for e in removed if (labels.pred_to_gt.get(e[0]), labels.pred_to_gt.get(e[1])) in labels.gt_edges]
            fully_matched_nontrue = [e for e in removed if e not in true_removed and e[0] in labels.pred_to_gt and e[1] in labels.pred_to_gt]
            cache[stem, key] = {'stem': stem, 'selected': key, 'score': row, 'added': added, 'removed': removed,
                                'removed_gt_true_edges': true_removed,
                                'removed_fully_matched_nontrue_edges': fully_matched_nontrue,
                                'removed_partially_or_unmatched_edges': [e for e in removed if e not in true_removed and e not in fully_matched_nontrue]}
    for mask in range(1 << len(events)):
        selected = {e['index'] for e in events if mask & (1 << e['index'])}
        chosen = [cache[stem, tuple(e['index'] for e in local if e['index'] in selected)] for stem, (_, _, _, local) in by_stem.items()]
        score = aggregate_official([r['score'] for r in chosen])
        prefixes = {p: aggregate_official([r['score'] for r in chosen if r['stem'].startswith(p)]) for p in ('44b6', '6bba')}
        cases.append({'mask': mask, 'events': sorted(selected), 'aggregate': score,
                      'delta_proxy': score['proxy_score'] - base_aggregate['proxy_score'], 'per_prefix': prefixes})
    best, worst = max(cases, key=lambda r: r['delta_proxy']), min(cases, key=lambda r: r['delta_proxy'])
    result = {'scope': 'GT-assisted TRAIN-only counterfactual in a restricted seven-triple edit family; not a global upper bound, deployable policy or LB forecast.',
              'baseline': base_aggregate, 'baseline_per_movie': baseline, 'events': events, 'cases': cases,
              'per_movie_edits_and_scores': list(cache.values()), 'best': best, 'worst': worst, 'all_seven': cases[-1],
              'n_combinations': len(cases), 'input_sha256': hashes,
              'limitations': 'No nodes or coordinates changed. Does not enforce actual candidate/event generation, learned selection, geometry, timing or decoder objective; all graphs audited. Positive result requires a separate GT-blind policy and independent validation before any training authorization.'}
    for p, h in hashes.items():
        assert hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
    OUT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'baseline': base_aggregate, 'best': best, 'worst': worst, 'all_seven': cases[-1], 'n_combinations': len(cases)}, indent=2))


if __name__ == '__main__':
    main()

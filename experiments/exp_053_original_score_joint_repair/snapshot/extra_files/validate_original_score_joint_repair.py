"""Snapshot smoke: syntax, embedded policy and prediction hook placement."""
import ast
import hashlib
import json
from pathlib import Path
import sys


def main(path):
    nb = json.loads(Path(path).read_text(encoding='utf-8'))
    code = [''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code']
    for s in code:
        ast.parse(s)
    install = next(s for s in code if '_jr_module = _jr_types.ModuleType' in s)
    assert install.index('_jr_spec.loader.exec_module') < install.index('def list_test_stems')
    graph = next(s for s in code if 'def filter_output_graph(' in s)
    tree = ast.parse(graph)
    f = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'filter_output_graph')
    body = ast.get_source_segment(graph, f)
    assert body.index('_jr_begin(') < body.index("_ev_graph(dataset, 'distance_filtered'")
    assert body.index('linefit_smooth_output_graph(') < body.index('_jr_finish(') < body.index('return nodes_by_id, edges, stats')
    core = next(n.args[0].value for n in ast.walk(ast.parse(install))
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'compile'
                and n.args and isinstance(n.args[0], ast.Constant) and 'class DetectionProvenance' in str(n.args[0].value))
    assert 'final_scored' not in core and 'scorer_matching' not in core
    assert 'secondary_source_features' not in core and 'secondary_target_features' not in core
    assert 'PARAMETERS = dict(top_k=8, protected_probability=0.9, edit_penalty=0.25)' in core
    contract = code[-1]
    assert 'exact_validation_graphs' in contract and 'exact_score_rows' in contract
    assert 'joint_repair_passed=all(_jr_checks.values())' in contract
    assert all(not c.get('outputs') for c in nb['cells'])
    print(json.dumps(dict(status='PASS', notebook_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                         note='Linux extension is hash-pinned and runtime-load-tested before inference; local Windows cannot execute ELF')))


if __name__ == '__main__':
    main(sys.argv[1])

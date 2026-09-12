"""Static snapshot smoke and instrumentation erasure equivalence checks."""
import ast
import copy
import json
import sys
from pathlib import Path
try:
    from .build_tracklet_evidence import build, source, PARENT, ROOT, patch_predictor
except ImportError:
    from build_tracklet_evidence import build, source, PARENT, ROOT, patch_predictor

class EraseObservation(ast.NodeTransformer):
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id.startswith('_ev_'):
            return None
        return self.generic_visit(node)

    def visit_Assign(self, node):
        if all(isinstance(t, ast.Name) and t.id.startswith('_ev_') for t in node.targets):
            return None
        return self.generic_visit(node)

def functions(text, erase=False):
    tree = ast.parse(text)
    if erase:
        tree = EraseObservation().visit(tree)
    return {n.name: ast.dump(n, include_attributes=False) for n in tree.body
            if isinstance(n, ast.FunctionDef)}

def validate(path):
    nb = json.loads(Path(path).read_text(encoding='utf-8'))
    assert nb == build(), 'Notebook differs from deterministic build'
    parent = json.loads(PARENT.read_text(encoding='utf-8'))
    for index in (2, 3, 4, 5, 6, 9, 10, 13):
        assert source(nb['cells'][index]) == source(parent['cells'][index]), 'Frozen cell changed: %s' % index
    for index in (7, 8, 11, 12):
        before = functions(source(parent['cells'][index]))
        after = functions(source(nb['cells'][index]), erase=True)
        assert all(after[name] == body for name, body in before.items()), 'Algorithm changed'
    # The only selector-cell addition enables observation before frozen inference.
    assert source(nb['cells'][11]).split('\n', 2)[2] == source(parent['cells'][11])
    predictor = (ROOT / 'experiments/repro_041_public_0941_motion_ema/artifacts/tracking_repo/scripts/predict_unet_transformer.py').read_text(encoding='utf-8')
    before, after = functions(predictor), functions(patch_predictor(predictor), erase=True)
    assert all(after[k] == v for k, v in before.items()), 'Worker algorithm changed'
    for c in nb['cells']:
        if c['cell_type'] == 'code':
            ast.parse(source(c))
            assert c['outputs'] == []
    assert sum(source(c).count('__CONTROLLER_EXPERIMENT_ID__') for c in nb['cells']) == 1
    return dict(passed=True, frozen_algorithm_ast=True, frozen_selector=True,
                frozen_scorer=True, runtime_exact_bytes_gate=True)

if __name__ == '__main__':
    print(json.dumps(validate(sys.argv[1])))

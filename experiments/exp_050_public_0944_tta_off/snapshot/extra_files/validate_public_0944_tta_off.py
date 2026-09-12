"""Snapshot smoke: frozen source, scorer and algorithmic-change boundaries."""
import ast
import json
import sys
from pathlib import Path

try:
    from .build_public_0944_tta_off import build, source, PARENT
except ImportError:
    from build_public_0944_tta_off import build, source, PARENT

def functions(text):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}

def validate(path):
    nb=json.loads(Path(path).read_text(encoding='utf-8'))
    assert nb == build(), 'Snapshot differs from deterministic single-variable build'
    parent=json.loads(PARENT.read_text(encoding='utf-8'))
    assert nb['cells'][4] == parent['cells'][4], 'Frozen selection/inference changed'
    old=functions(source(parent['cells'][5])); new=functions(source(nb['cells'][5]))
    assert all(new[k]==v for k,v in old.items()), 'Frozen scorer changed'
    old=functions(source(parent['cells'][2])); new=functions(source(nb['cells'][2]))
    assert old==new, 'Inference/postprocessing functions changed'
    text=source(nb['cells'][2])
    assert "os.environ['BIOHUB_EDGE_FEATURE_TTA'] = '0'" in text
    assert 'MOTION_RELINK_EMA_ALPHA' not in text
    assert 'valid_tta_off_receipts(_tta_receipts)' in source(nb['cells'][6])
    for node in ast.parse(text).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_et_new' for t in node.targets):
            ast.parse(ast.literal_eval(node.value.args[0]))
    for c in nb['cells']:
        if c['cell_type']=='code':
            ast.parse(source(c)); assert not c['outputs']
    assert sum(source(c).count('__CONTROLLER_EXPERIMENT_ID__') for c in nb['cells'])==1
    return dict(passed=True, frozen_scorer=True, frozen_selector=True, upstream_motion=True,
                algorithmic_change='edge_feature_tta_1_to_0', graph_export_after_scoring=True)

if __name__=='__main__':
    print(json.dumps(validate(sys.argv[1])))

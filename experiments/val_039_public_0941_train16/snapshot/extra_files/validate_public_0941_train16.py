"""Check exact adaptation and frozen scoring without running GPU inference."""
from __future__ import annotations
import argparse
import ast
import json
from pathlib import Path
from build_public_0941_train16 import ANCHOR, PARENT, build, source


def functions(text):
    return {node.name: ast.dump(node, include_attributes=False)
            for node in ast.parse(text).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def validate(path):
    actual = json.loads(Path(path).read_text(encoding='utf-8'))
    expected = build()
    if actual != expected:
        raise ValueError('Notebook differs from deterministic reviewed adaptation')
    code = [c for c in actual['cells'] if c['cell_type'] == 'code']
    parent = json.loads(PARENT.read_text(encoding='utf-8'))['cells']
    anchor = json.loads(ANCHOR.read_text(encoding='utf-8'))['cells']
    for index in range(5):
        assert source(code[index + 1]) == source(parent[index]), 'Inference source drift'
    before, after = functions(source(parent[5])), functions(source(code[6]))
    assert {k: v for k, v in before.items() if k != 'load_deepcenter_veto_detector'} == {
        k: v for k, v in after.items() if k != 'load_deepcenter_veto_detector'}, 'Postprocessing changed'
    assert functions(source(code[10])) == functions(source(anchor[20])), 'Frozen scoring functions changed'
    assert functions(source(code[9])) == functions(source(anchor[18])), 'Frozen selector/runner changed'
    text = '\n'.join(source(c) for c in actual['cells'])
    assert text.count('__CONTROLLER_EXPERIMENT_ID__') == 1
    assert not any('\u4e00' <= ch <= '\u9fff' or '\u0400' <= ch <= '\u04ff' for ch in text)
    for c in code:
        ast.parse(source(c))
        assert c['outputs'] == [] and c['execution_count'] is None
    return {'passed': True, 'cells': len(actual['cells']), 'scorer_functions': len(functions(source(anchor[20]))),
            'inference_preserved': True, 'saved_errors': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('notebook', type=Path)
    print(json.dumps(validate(parser.parse_args().notebook), indent=2))

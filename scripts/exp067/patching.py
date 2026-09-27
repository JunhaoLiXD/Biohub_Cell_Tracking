"""SHA-pinned parent integration and local replay of its actual source patch chain."""
from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / 'experiments/exp_064_x138_verbatim_repro/snapshot/source/biohub-x138.ipynb'
PARENT_SHA = '6b655e39bbfd2d3d6c762badea69847d3f00f5b548f385cb01b07ee2600fde6d'
REFERENCE = ROOT / 'references/biohub-tracking-support-pack/repo/scripts/predict_unet_transformer.py'


def once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f'exp067 anchor count {source.count(old)}: {old[:100]!r}')
    return source.replace(old, new, 1)


def parent_notebook():
    data = PARENT.read_bytes()
    if hashlib.sha256(data).hexdigest() != PARENT_SHA:
        raise ValueError('exp064 parent notebook SHA mismatch')
    return json.loads(data)


def replay_parent():
    """Execute only parent SOURCE patches against a scratch reference, never inference."""
    source = ''.join(parent_notebook()['cells'][4]['source'])
    tree = ast.parse(source)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'scripts').mkdir()
        target = root / 'scripts/predict_unet_transformer.py'
        target.write_text(REFERENCE.read_text(encoding='utf-8'), encoding='utf-8')
        env = dict(os.environ, BIOHUB_BIDIRECTIONAL_EDGE_WEIGHT='0.15',
                   BIOHUB_CACHE_DIR=str(root / 'cache'), BIOHUB_CACHE_EDGE_THRESHOLD='1.0')
        ns = {'REPO_DIR': root, 'WORKING_DIR': root, 'Path': Path,
              'os': SimpleNamespace(environ=env), 'json': json}
        picked = [n for n in tree.body if 11 <= n.lineno <= 308 or 484 <= n.lineno <= 499
                  or 522 <= n.lineno <= 533]
        with contextlib.redirect_stdout(io.StringIO()):
            # The last parent print reads V1284_MODE; no checkpoint or CUDA access occurs here.
            env['V1284_MODE'] = 'candidate'
            exec(compile(ast.Module(body=picked, type_ignores=[]), '<parent patches>', 'exec'), ns)
        result = target.read_text(encoding='utf-8')
        compile(result, '<parent predictor>', 'exec')
        if 'low_coords' not in result or '_v1284_refine(ds_path' not in result:
            raise ValueError('parent patch chain failed or silently skipped cache hook')
        return result


def patch_predictor(source):
    source = once(source, 'import tracksdata as td\n',
                  'import tracksdata as td\nfrom scripts.exp067 import bridge as _x67, export_hooks as _x67h\n')
    source = once(source, '    zarr_arr = ',
                  "    if _x67.enabled(): _x67h.begin_video(ds_path.stem)\n    zarr_arr = ")
    source = once(source, '                coord_offset[t] = (global_node_count, global_node_count + len(arr))',
                  '                if _x67.enabled(): _x67.first_seen(locals())\n'
                  '                coord_offset[t] = (global_node_count, global_node_count + len(arr))')
    source = once(source, '            candidates = sorted(',
                  '            if _x67.enabled(): _x67.pair(locals())\n            candidates = sorted(')
    source = once(source, '    edges: list[tuple[int, int, float, float]],\n) -> td.graph.InMemoryGraph:',
                  '    edges: list[tuple[int, int, float, float]],\n    exp067_stem=None,\n) -> td.graph.InMemoryGraph:')
    source = once(source, '    if edges:\n        graph.add_edge_attr_key',
                  '    if _x67.enabled(): _x67h.record_graph_node_ids(exp067_stem, node_ids)\n\n'
                  '    if edges:\n        graph.add_edge_attr_key')
    source = once(source, '        graph = build_graph(coords, edges)\n',
                  '        graph = build_graph(coords, edges, exp067_stem=Path(name).stem)\n'
                  '        if _x67.enabled(): _x67.finish_predictor(dict(locals(), __file__=__file__))\n')
    compile(source, '<exp067 predictor>', 'exec')
    return source


def patch_notebook(mode='control', stems=(), checkpoint='', runtime_config=None):
    if mode not in ('control', 'export', 'decode'):
        raise ValueError(mode)
    if mode == 'export' and (not stems or len(set(stems)) != len(stems)):
        raise ValueError('export requires distinct explicit TRAIN stems')
    if mode == 'decode' and not checkpoint:
        raise ValueError('decode requires trained checkpoint path')
    nb = copy.deepcopy(parent_notebook())
    edits = []
    def change(index, old, new):
        src = ''.join(nb['cells'][index]['source'])
        nb['cells'][index]['source'] = once(src, old, new)
        edits.append((index, old, new))
    change(4, 'start_time = time.time()\n',
           'from scripts.exp067.patching import patch_predictor as _x67patch\n'
           '_ps.write_text(_x67patch(_ps.read_text()), encoding="utf-8")\nstart_time = time.time()\n')
    change(5, '    _stage_t0 = _time.time()\n',
           '    _stage_t0 = _time.time()\n    _x67.tag_original(nodes_by_id, dataset)\n')
    change(5, '            inserted_ids.append(node_id)\n',
           '            if _x67.enabled(): nodes_by_id[node_id]["_exp067_origin"] = 2\n'
           '            inserted_ids.append(node_id)\n')
    # Restrict the return anchor to the following unique global initialization.
    old = '    return nodes_by_id, edges, stats\n\n\nDEEPCENTER_VETO_DETECTOR'
    change(5, old, '    nodes_by_id, edges = _x67.final_stage(nodes_by_id, edges, stats, dataset)\n' + old)
    change(5, '            filter_stats["deadline_degraded"]',
           '            _x67rt.raise_if_fatal()\n            filter_stats["deadline_degraded"]')
    # The parent explicitly overwrites PYTHONPATH for each subprocess.
    for index in (4, 7):
        source = ''.join(nb['cells'][index]['source'])
        old_env = '"PYTHONPATH": "src"'
        if source.count(old_env) != 2:
            raise ValueError('exp067 subprocess environment anchors changed')
        change(index, source, source.replace(old_env,
               '"PYTHONPATH": os.environ["PYTHONPATH"] + os.pathsep + "src"'))
    # Exports operate on explicitly selected TRAIN stems, never a label-selected sweep.
    if mode == 'export':
        source = ''.join(nb['cells'][4]['source'])
        start = source.index('start_time = time.time()\n')
        change(4, source[start:], 'predict_seconds = 0.0\nprint("exp067: TEST prediction skipped")\n')
        change(5, 'write_test_submission("base")\n',
               'print("exp067 TRAIN export: competition TEST inference skipped")\n')
        source = ''.join(nb['cells'][6]['source'])
        change(6, source, 'print("exp067: TEST submission guard inapplicable to TRAIN export")\n')
        source = ''.join(nb['cells'][7]['source'])
        a = source.index('val_stems: list[str] = []')
        b = source.index('def _merge_validator_shards')
        replacement = ('val_stems = list(_x67_stems)\n'
            'if set(val_stems) & set(test_stems): raise ValueError("exp067 TRAIN/TEST overlap")\n'
            'for _stem in val_stems:\n'
            '    if not (TRAIN_DIR / f"{_stem}.zarr").exists() or not (TRAIN_DIR / f"{_stem}.geff").exists():\n'
            '        raise FileNotFoundError(f"exp067 missing explicit TRAIN movie {_stem}")\n'
            'os.environ["BIOHUB_EXP067_SPLIT"] = "train"\n\n\n')
        change(7, source[a:b], replacement)
        change(9, '            gt_nodes_plain, gt_edges_plain, t_true = VAL_GT[stem]\n',
               '            _x67rt.raise_if_fatal()\n'
               '            gt_nodes_plain, gt_edges_plain, t_true = VAL_GT[stem]\n'
               '            _x67.label_stage(stem, processed_nodes, gt_nodes_plain, gt_edges_plain, t_true)\n')
        source = ''.join(nb['cells'][10]['source'])
        change(10, source, 'print("exp067: sweep disabled; fixed exp064 parent policy")\n')
    files = {p.name: p.read_text(encoding='utf-8') for p in (ROOT / 'scripts/exp067').glob('*.py')}
    bootstrap = ('# exp067 additive runtime bundle; no dependency installation or remote execution\n'
        'import os, sys, json\nfrom pathlib import Path\n'
        '_x67root = Path("/kaggle/working/exp067_runtime")\n'
        '(_x67root / "scripts/exp067").mkdir(parents=True, exist_ok=True)\n'
        '(_x67root / "scripts/__init__.py").write_text("", encoding="utf-8")\n'
        f'_x67files = {files!r}\n'
        'for _name, _text in _x67files.items():\n'
        '    (_x67root / "scripts/exp067" / _name).write_text(_text, encoding="utf-8")\n'
        'sys.path.insert(0, str(_x67root))\n'
        'os.environ["PYTHONPATH"] = str(_x67root) + os.pathsep + os.environ.get("PYTHONPATH", "")\n'
        'from scripts.exp067 import bridge as _x67, runtime as _x67rt\n'
        f'_x67_stems = {list(stems)!r}\n'
        f'os.environ["BIOHUB_EXP067_EXPORT"] = {str(int(mode != "control"))!r}\n'
        f'os.environ["BIOHUB_EXP067_ENABLE"] = {str(int(mode == "decode"))!r}\n'
        f'os.environ["BIOHUB_EXP067_LABELS"] = {str(int(mode == "export"))!r}\n'
        'os.environ["BIOHUB_EXP067_LABEL_STEMS"] = ",".join(_x67_stems)\n'
        'os.environ["BIOHUB_EXP067_EXPORT_DIR"] = "/kaggle/working/exp067_export"\n'
        'os.environ["BIOHUB_EXP067_SPLIT"] = "test"\n'
        f'os.environ["BIOHUB_EXP067_CKPT"] = {checkpoint!r}\n'
        f'os.environ["BIOHUB_VALIDATOR_ENABLE"] = {str(int(mode == "export"))!r}\n'
        f'os.environ["BIOHUB_EXP067_CONFIG_JSON"] = {json.dumps(runtime_config or {})!r}\n'
        '_x67rt.clear_fatal()\n')
    # After parent cell0 config, before any inference. Undo edits to prove all original cell text preserved.
    restored = copy.deepcopy(nb)
    for index, old, new in reversed(edits):
        restored['cells'][index]['source'] = once(''.join(restored['cells'][index]['source']), new, old)
    parent = parent_notebook()
    if any(''.join(a['source']) != ''.join(b['source']) for a, b in zip(restored['cells'], parent['cells'])):
        raise AssertionError('exp067 reverse-patch parity failed')
    nb['cells'].insert(1, {'cell_type': 'code', 'metadata': {}, 'execution_count': None, 'outputs': [], 'source': bootstrap})
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            cell['outputs'] = []
            cell['execution_count'] = None
            compile(''.join(cell['source']), '<exp067 notebook cell>', 'exec')
    return nb

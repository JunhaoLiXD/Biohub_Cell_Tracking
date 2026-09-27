"""Static resolution of the frozen exp064 parent's effective configuration.

The exp067b admission review found that the runtime gate checked *environment
assignments* before the parent's postprocessing globals resolve, and that the final
metrics merely *recorded* those globals without asserting them. Fixing that needs an
expected table that is derived from the frozen parent source itself rather than
retyped by hand, so this module evaluates the parent notebook's own assignments with
a deliberately tiny, side-effect-free interpreter.

Only expressions the parent actually uses for configuration are supported: literals,
literal containers, f-strings over already-resolved names, ``os.environ.get``, the
``float``/``int``/``str``/``bool`` casts, ``.strip()``/``.lower()``/``.upper()`` and
``==``/``!=``. Anything else -- paths discovered from Kaggle mounts, loaded model
bundles, comprehensions, wall clock -- is reported as unresolved with its source text so
the caller can declare, rather than silently drop, what it does not assert.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT_NOTEBOOK = ROOT / 'experiments/exp_064_x138_verbatim_repro/snapshot/source/biohub-x138.ipynb'

# Wall clock, not a frozen model configuration.
WALL_CLOCK_ENV_KEYS = {'BIOHUB_KERNEL_START_TS'}
# Cells whose module-level uppercase assignments carry effective configuration.
CONFIG_CELLS = (2, 3, 5, 7)


class Unresolved(Exception):
    pass


def parent_cells() -> list[str]:
    notebook = json.loads(PARENT_NOTEBOOK.read_text(encoding='utf-8'))
    return [''.join(cell['source']) for cell in notebook['cells']]


def _literal(node: ast.AST):
    return ast.literal_eval(node)


def frozen_environment(cells: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """Return (literal env values, runtime-derived env keys -> their source text).

    Assignments are walked in notebook order so a later cell overrides an earlier one,
    exactly as the parent executes them.
    """
    literal: dict[str, str] = {}
    derived: dict[str, str] = {}
    for source in cells:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Assign) and len(node.targets) == 1):
                continue
            target = node.targets[0]
            if not (isinstance(target, ast.Subscript)
                    and ast.unparse(target.value).endswith('environ')):
                continue
            try:
                key = _literal(target.slice)
            except ValueError:
                continue  # e.g. the disabled sweep's dynamic "BIOHUB_" + key writes
            if key in WALL_CLOCK_ENV_KEYS:
                continue
            value = node.value
            if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) \
                    and value.func.id == 'str' and len(value.args) == 1:
                try:
                    literal[key] = str(_literal(value.args[0]))
                    derived.pop(key, None)
                    continue
                except ValueError:
                    derived[key] = ast.unparse(value)
                    literal.pop(key, None)
                    continue
            try:
                literal[key] = _literal(value)
                derived.pop(key, None)
            except ValueError:
                derived[key] = ast.unparse(value)
                literal.pop(key, None)
    return literal, derived


def assigned_environment_keys(cells: list[str]) -> set[str]:
    """EVERY environment key the parent assigns, with no exclusions at all.

    Distinct from :func:`frozen_environment`, which drops wall clock because its *value* cannot be
    asserted. A key whose value we decline to assert is still a key the parent legitimately sets,
    so the two sets must not be conflated: doing so made the exp067c v1 run fail its own
    stray-key check on ``BIOHUB_KERNEL_START_TS``, which cell 0 assigns and which is therefore
    expected to be present.
    """
    keys: set[str] = set()
    for source in cells:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Assign) and len(node.targets) == 1):
                continue
            target = node.targets[0]
            if not (isinstance(target, ast.Subscript)
                    and ast.unparse(target.value).endswith('environ')):
                continue
            try:
                keys.add(_literal(target.slice))
            except ValueError:
                continue  # the disabled sweep's dynamic "BIOHUB_" + key writes
    return keys


def _evaluator(env: dict[str, str], scope: dict[str, object], reads: set[str] | None = None):
    def evaluate(node: ast.AST):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in scope:
                return scope[node.id]
            raise Unresolved(node.id)
        if isinstance(node, ast.JoinedStr):
            out = ''
            for part in node.values:
                if isinstance(part, ast.Constant):
                    out += str(part.value)
                elif isinstance(part, ast.FormattedValue) and part.format_spec is None \
                        and part.conversion == -1:
                    out += str(evaluate(part.value))
                else:
                    raise Unresolved('formatted value')
            return out
        if isinstance(node, (ast.List, ast.Tuple)):
            items = []
            for element in node.elts:
                if isinstance(element, ast.Starred):
                    items.extend(evaluate(element.value))
                else:
                    items.append(evaluate(element))
            return items if isinstance(node, ast.List) else tuple(items)
        if isinstance(node, ast.Dict):
            if any(key is None for key in node.keys):
                raise Unresolved('dict unpacking')
            return {evaluate(key): evaluate(value)
                    for key, value in zip(node.keys, node.values)}
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, right = evaluate(node.left), evaluate(node.comparators[0])
            if isinstance(node.ops[0], ast.Eq):
                return left == right
            if isinstance(node.ops[0], ast.NotEq):
                return left != right
            raise Unresolved('comparison operator')
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in ('float', 'int', 'str', 'bool'):
                cast = {'float': float, 'int': int, 'str': str, 'bool': bool}[func.id]
                return cast(*[evaluate(arg) for arg in node.args])
            if isinstance(func, ast.Attribute):
                owner = ast.unparse(func.value)
                if owner.endswith('environ') and func.attr == 'get':
                    key = evaluate(node.args[0])
                    if reads is not None:
                        reads.add(key)
                    default = evaluate(node.args[1]) if len(node.args) > 1 else None
                    return env.get(key, default)
                if func.attr in ('strip', 'lower', 'upper'):
                    base = evaluate(func.value)
                    if not isinstance(base, str):
                        raise Unresolved('string method on non-string')
                    return getattr(base, func.attr)(*[evaluate(arg) for arg in node.args])
        raise Unresolved(ast.unparse(node))
    return evaluate


def resolved_globals(cells: list[str], env: dict[str, str]) -> tuple[dict[str, object], dict[str, str]]:
    """Return (uppercase globals resolvable from the frozen configuration, unresolved -> source)."""
    scope: dict[str, object] = {}
    resolved: dict[str, object] = {}
    unresolved: dict[str, str] = {}
    for index in CONFIG_CELLS:
        # A cell can only see environment assignments that have already executed. Resolve
        # against that prefix and fail the build if any key it reads is rewritten later,
        # rather than silently resolving a global against a value it never saw.
        prefix_env, _ = frozen_environment(cells[: index + 1])
        reads: set[str] = set()
        evaluate = _evaluator(prefix_env, scope, reads)
        for node in ast.parse(cells[index]).body:
            if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)):
                continue
            name = node.targets[0].id
            if not name.isupper() or name.startswith('_'):
                continue
            try:
                value = evaluate(node.value)
            except Unresolved as exc:
                unresolved[name] = f'cell{index}: {exc}'
                continue
            if isinstance(value, (str, int, float, bool, list, tuple, dict)):
                scope[name] = value
                resolved[name] = value
            else:
                unresolved[name] = f'cell{index}: non-primitive {type(value).__name__}'
        rewritten = sorted(key for key in reads
                           if key in env and prefix_env.get(key) != env[key])
        if rewritten:
            raise Unresolved(
                f'cell{index} globals read environment keys rewritten by a later cell: {rewritten}')
    return resolved, unresolved

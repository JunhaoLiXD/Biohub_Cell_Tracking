"""exp_054 smoke: exp_053 checks plus a clean-namespace solver probe."""

import ast
import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".private/runtime/graph_pilot"))

try:
    from validate_original_score_joint_repair import main as validate_base
except ModuleNotFoundError:
    from scripts.validate_original_score_joint_repair import main as validate_base


def _name_in(node, name):
    return any(isinstance(item, ast.Name) and item.id == name for item in ast.walk(node))


def execute_clean_namespace_solver_probe(notebook_path):
    """Execute the emitted NumPy import and solver self-test with no ambient globals."""
    notebook = json.loads(Path(notebook_path).read_text(encoding="utf-8"))
    code = ["".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"]
    install = next(source for source in code if "_jr_module = _jr_types.ModuleType" in source)
    tree = ast.parse(install)

    numpy_import = next(
        node for node in tree.body
        if isinstance(node, ast.Import)
        and any(alias.name == "numpy" and alias.asname == "_jr_np" for alias in node.names)
    )
    solver_call = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Tuple)
                and any(isinstance(item, ast.Name) and item.id == "_jr_r" for item in target.elts)
                for target in node.targets)
    )
    solver_assert = next(
        node for node in tree.body
        if isinstance(node, ast.Assert) and _name_in(node, "_jr_r") and _name_in(node, "_jr_c")
    )
    assert tree.body.index(numpy_import) < tree.body.index(solver_call) < tree.body.index(solver_assert)

    core = next(
        node.args[0].value for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "compile" and node.args
        and isinstance(node.args[0], ast.Constant)
        and "class DetectionProvenance" in str(node.args[0].value)
    )
    module = types.ModuleType("_clean_namespace_original_joint")
    sys.modules[module.__name__] = module
    try:
        exec(compile(core, "<clean-namespace-original-score-repair>", "exec"), module.__dict__)
        probe = ast.fix_missing_locations(ast.Module(
            body=[numpy_import, solver_call, solver_assert], type_ignores=[]
        ))
        namespace = {"_jr_module": module}
        exec(compile(probe, "<clean-namespace-solver-probe>", "exec"), namespace)
        assert namespace["_jr_r"].tolist() == [0, 1]
        assert namespace["_jr_c"].tolist() == [1, 0]
    finally:
        sys.modules.pop(module.__name__, None)


def main(path):
    validate_base(path)
    execute_clean_namespace_solver_probe(path)
    print(json.dumps({"status": "PASS", "clean_namespace_solver_probe": True}))


if __name__ == "__main__":
    main(sys.argv[1])

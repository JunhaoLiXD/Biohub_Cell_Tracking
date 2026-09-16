"""exp_054 smoke: exp_053 checks plus a clean-namespace solver probe."""

import ast
import json
from pathlib import Path
import sys
import types

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

    class _ArrayResult(list):
        def tolist(self):
            return list(self)

    fake_numpy = types.ModuleType("numpy")
    fake_numpy.array = lambda value: value
    module = types.SimpleNamespace()

    def fake_solver(matrix, *, maximize):
        assert matrix == [[1.0, 3.0], [4.0, 1.0]]
        assert maximize is True
        return _ArrayResult([0, 1]), _ArrayResult([1, 0])

    module.linear_sum_assignment = fake_solver
    previous_numpy = sys.modules.get("numpy")
    sys.modules["numpy"] = fake_numpy
    try:
        probe = ast.fix_missing_locations(ast.Module(
            body=[numpy_import, solver_call, solver_assert], type_ignores=[]
        ))
        namespace = {"_jr_module": module}
        exec(compile(probe, "<clean-namespace-solver-probe>", "exec"), namespace)
        assert namespace["_jr_r"].tolist() == [0, 1]
        assert namespace["_jr_c"].tolist() == [1, 0]
    finally:
        if previous_numpy is None:
            sys.modules.pop("numpy", None)
        else:
            sys.modules["numpy"] = previous_numpy


def main(path):
    validate_base(path)
    execute_clean_namespace_solver_probe(path)
    print(json.dumps({"status": "PASS", "clean_namespace_solver_probe": True}))


if __name__ == "__main__":
    main(sys.argv[1])

from pathlib import Path

from scripts.validate_original_score_joint_repair_v2 import execute_clean_namespace_solver_probe


def test_exp055_solver_probe_executes_without_ambient_numpy():
    root = Path(__file__).resolve().parents[1]
    execute_clean_namespace_solver_probe(root / ".private/current/original_score_joint_repair_v3.ipynb")

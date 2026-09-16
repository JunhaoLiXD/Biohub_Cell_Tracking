"""Build the exp_054 bootstrap-only repair without changing exp_053 behavior."""

from build_original_score_joint_repair import build as _build
import build_original_score_joint_repair as _base


_base.TARGET = _base.ROOT / ".private/current/original_score_joint_repair_v2.ipynb"
_base.EXPERIMENT = "exp_054_original_score_joint_bootstrap_fix"
_base.SOLVER_NUMPY_IMPORT = "import numpy as _jr_np\n"
_base.SOLVER_NUMPY_NAME = "_jr_np"


def build():
    return _build()


if __name__ == "__main__":
    print(build())

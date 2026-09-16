"""Build exp_055 with the exp_054 remote behavior and portable admission smoke."""

from build_original_score_joint_repair import build as _build
import build_original_score_joint_repair as _base


_base.TARGET = _base.ROOT / ".private/current/original_score_joint_repair_v3.ipynb"
_base.EXPERIMENT = "exp_055_original_score_joint_bootstrap_smoke_fix"
_base.SOLVER_NUMPY_IMPORT = "import numpy as _jr_np\n"
_base.SOLVER_NUMPY_NAME = "_jr_np"


def build():
    return _build()


if __name__ == "__main__":
    print(build())

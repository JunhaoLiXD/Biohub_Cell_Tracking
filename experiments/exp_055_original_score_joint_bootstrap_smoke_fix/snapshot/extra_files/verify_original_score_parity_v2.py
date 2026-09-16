"""Replay exp_054 parity into a new output directory without changing fixtures."""

from pathlib import Path

import verify_original_score_parity as _base


_base.OUT = Path(__file__).resolve().parents[1] / "experiments/local_054_original_score_final_stage_parity"


if __name__ == "__main__":
    _base.main()

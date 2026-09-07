"""Collect the unchanged public reproduction through the deterministic adapter."""
import json
from _bootstrap import PROJECT_ROOT
from experiment_controller.public_copy import collect

if __name__ == "__main__":
    print(json.dumps(collect(PROJECT_ROOT), indent=2))

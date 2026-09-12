"""Collect the path-only edited public 0.946 reproduction."""
import json
from _bootstrap import PROJECT_ROOT
from experiment_controller.public_0946_copy import collect

if __name__ == "__main__":
    print(json.dumps(collect(PROJECT_ROOT), indent=2))

import csv
import json

import pytest

from experiment_controller.core import ControllerError, create_experiment, load_config
from experiment_controller.kaggle import prepare_kernel_directory
from experiment_controller.public_copy import aggregate, read_validator


def test_native_aggregation_weights_edges_and_pools_divisions():
    rows = [
        dict(stem="44b6_a", weight=1, adjusted_edge_jaccard=0.5, div_tp=1, div_fp=0, div_fn=0),
        dict(stem="6bba_b", weight=3, adjusted_edge_jaccard=0.9, div_tp=0, div_fp=1, div_fn=2),
    ]
    result = aggregate(rows)
    assert result["adjusted_edge_jaccard"] == pytest.approx(0.8)
    assert result["division_jaccard"] == pytest.approx(0.25)
    assert result["primary_metric"] == pytest.approx(0.825)


@pytest.mark.parametrize("bad", ["missing_specimen", "nan"])
def test_native_csv_rejects_incomplete_or_nonfinite_evidence(tmp_path, bad):
    path = tmp_path / "validator_results.csv"
    stems = ["44b6_a", "44b6_b", "6bba_a", "6bba_b"]
    if bad == "missing_specimen":
        stems[-1] = "44b6_c"
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["stem", "weight", "adjusted_edge_jaccard", "div_tp", "div_fp", "div_fn"])
        for stem in stems:
            writer.writerow([stem, 10, "nan" if bad == "nan" else 0.9, 1, 0, 0])
    with pytest.raises(ControllerError):
        read_validator(path)


def test_public_docker_pin_and_source_bytes_survive_staging(project_factory):
    root, config_path = project_factory()
    _, config = load_config(config_path, root)
    config["kaggle"]["docker_image"] = "gcr.io/example/python@sha256:abc"
    import yaml
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    record = create_experiment(config_path, root=root)
    directory, _ = prepare_kernel_directory(root, record, config)
    metadata = json.loads((directory / "kernel-metadata.json").read_text())
    assert metadata["docker_image"] == config["kaggle"]["docker_image"]
    assert metadata["docker_image_pinning_type"] == "original"
    assert (directory / "run.ipynb").read_bytes() == (root / "src/run.ipynb").read_bytes()

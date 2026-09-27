"""Training CLI. Fixed schedule; no held-out selection of any kind (codex_challenge_v1 item 7).

There is no early stopping, no checkpoint selection, no calibration pass and no hyperparameter search
against the held-out manifest. The held-out stems are scored **once**, after the schedule ends, and the
numbers that come out are reported as what they are. Any inner validation draws from TRAINING stems
only (``--inner-val-frac``).

Usage::

    python -m scripts.exp067.train \
        --export-dir artifacts/exp067/export \
        --label-dir  artifacts/exp067/labels \
        --splits     configs/exp067_splits.json \
        --out        artifacts/exp067/ckpt/fold.pt
"""

from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

import numpy as np
import torch
from torch import nn

from . import checkpoint, provenance, supervise
from . import features as F
from .config import Exp067Config
from .errors import Exp067InsufficientSupervision
from .model import JointLineageScorer, Normalizer
from .runtime import assert_environment


def set_determinism(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(1)


def load_stem_samples(
    export_dir: Path,
    label_dir: Path | None,
    stems: Sequence[str],
    config: Exp067Config,
) -> tuple[list[supervise.Sample], int]:
    samples: list[supervise.Sample] = []
    channels = 0
    for stem in sorted(stems):
        graph = provenance.load_final_graph(export_dir / f"{stem}.final.npz")
        evidence = provenance.load_evidence(export_dir / f"{stem}.npz")
        if evidence.manifest.get('split') != 'train':
            raise ValueError(f'{stem}: supervision requires an explicit TRAIN export')
        if channels and channels != evidence.emb_channels:
            raise ValueError('embedding width differs across movies')
        channels = channels or evidence.emb_channels
        labels = None
        if label_dir is not None:
            label_path = label_dir / f"{stem}.npz"
            if label_path.exists():
                labels = supervise.load_label_set(label_path)
                if labels.stem != stem:
                    raise ValueError('label stem mismatch')
            else:
                raise FileNotFoundError(label_path)
        stem_samples, _hyp, _ctx = supervise.build_stem_samples(graph, evidence, labels, config)
        samples.extend(stem_samples)
    return samples, channels


def masked_bce(logits: torch.Tensor, labels: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """Zero gradient on UNKNOWN. Returns a 0-d tensor; 0.0 when nothing is labelled."""
    if mask.numel() == 0 or not bool(mask.any()):
        return logits.sum() * 0.0
    selected = logits[mask]
    target = labels[mask].to(selected.dtype)
    return nn.functional.binary_cross_entropy_with_logits(selected, target, reduction="mean")


def fit_normalizer(samples: Sequence[supervise.Sample], token_width: int) -> Normalizer:
    """Statistics from the TRAINING samples only; stored in the checkpoint."""
    return Normalizer.fit(
        [s.tokens for s in samples],
        [s.edge_feats for s in samples if len(s.edge_feats)],
        [s.event_feats for s in samples if len(s.event_feats)],
        token_width,
    )


def evaluate_supervised(
    model: JointLineageScorer, normalizer: Normalizer, samples: Sequence[supervise.Sample]
) -> dict[str, float]:
    """Masked supervised metrics only. This is not the competition proxy; see evaluate.py."""
    model.eval()
    link_correct = link_total = event_correct = event_total = 0
    link_loss = event_loss = 0.0
    link_batches = event_batches = 0
    with torch.no_grad():
        for sample in samples:
            tokens = torch.from_numpy(normalizer.apply_tokens(sample.tokens))
            link, div = model(
                tokens,
                torch.from_numpy(sample.edge_local),
                torch.from_numpy(normalizer.apply_edges(sample.edge_feats)),
                torch.from_numpy(sample.event_local),
                torch.from_numpy(normalizer.apply_events(sample.event_feats)),
            )
            e_mask = torch.from_numpy(sample.edge_mask)
            if bool(e_mask.any()):
                target = torch.from_numpy(sample.edge_label.astype(np.float32))
                link_loss += float(masked_bce(link, target, e_mask))
                link_batches += 1
                predicted = (link[e_mask] > 0).to(torch.int8).numpy()
                link_correct += int((predicted == sample.edge_label[sample.edge_mask]).sum())
                link_total += int(sample.edge_mask.sum())
            v_mask = torch.from_numpy(sample.event_mask)
            if bool(v_mask.any()):
                target = torch.from_numpy(sample.event_label.astype(np.float32))
                event_loss += float(masked_bce(div, target, v_mask))
                event_batches += 1
                predicted = (div[v_mask] > 0).to(torch.int8).numpy()
                event_correct += int((predicted == sample.event_label[sample.event_mask]).sum())
                event_total += int(sample.event_mask.sum())
    return {
        "link_masked_bce": link_loss / max(link_batches, 1),
        "link_accuracy": link_correct / max(link_total, 1),
        "link_labelled": float(link_total),
        "event_masked_bce": event_loss / max(event_batches, 1),
        "event_accuracy": event_correct / max(event_total, 1),
        "event_labelled": float(event_total),
    }


def train(
    export_dir: Path,
    label_dir: Path,
    splits_path: Path,
    out_path: Path,
    config: Exp067Config,
    report_path: Path | None = None,
) -> dict[str, object]:
    assert_environment()
    cfg = config.train
    if cfg.epochs < 1 or cfg.max_seconds <= 0:
        raise ValueError("positive epochs and training walltime required")
    started = time.monotonic()
    set_determinism(cfg.seed)
    splits = supervise.load_splits(splits_path)
    import hashlib
    input_hashes = {}
    export_signature = None
    for stem in splits.train + splits.holdout:
        ev = provenance.load_evidence(export_dir / f'{stem}.npz')
        signature = {k: ev.manifest.get(k) for k in ('weights_sha256', 'predict_source_sha256')}
        if not all(signature.values()):
            raise ValueError(f'{stem}: missing frozen-backbone provenance')
        if export_signature is not None and signature != export_signature:
            raise ValueError('mixed frozen-backbone provenance')
        export_signature = signature
        for kind, path in [('evidence', export_dir / f'{stem}.npz'),
                           ('final', export_dir / f'{stem}.final.npz'),
                           ('labels', label_dir / f'{stem}.npz')]:
            input_hashes[f'{stem}:{kind}'] = hashlib.sha256(path.read_bytes()).hexdigest()

    train_stems, inner_val = supervise.inner_split(splits.train, cfg.inner_val_frac, cfg.seed)
    train_samples, channels = load_stem_samples(export_dir, label_dir, train_stems, config)
    counts = supervise.sample_counts(train_samples)

    if counts["link_positive"] < cfg.min_link_positives:
        raise Exp067InsufficientSupervision(
            f"{counts['link_positive']} unmasked link positives across {len(train_stems)} training "
            f"stem(s), below min_link_positives={cfg.min_link_positives}. Export more TRAIN stems; the "
            "validator's own 8-movie selection is not a data limit."
        )
    if counts["event_positive"] < cfg.min_division_positives:
        raise Exp067InsufficientSupervision(
            f"{counts['event_positive']} unmasked division positives across {len(train_stems)} training "
            f"stem(s), below min_division_positives={cfg.min_division_positives}. The division head is "
            "trainable only with annotated mothers whose BOTH daughters are matched."
        )

    if counts["link_negative"] < 1 or counts["event_negative"] < 1:
        raise Exp067InsufficientSupervision("Both heads require annotated negative examples")
    token_width = F.token_dim(channels)
    normalizer = fit_normalizer(train_samples, token_width)
    model = JointLineageScorer(channels, config.model)
    optimiser = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    scheduler = torch.optim.lr_scheduler.MultiStepLR(
        optimiser, milestones=list(cfg.lr_decay_at), gamma=cfg.lr_decay_gamma
    )

    order = list(range(len(train_samples)))
    rng = random.Random(cfg.seed)
    history: list[dict[str, float]] = []
    model.train()
    for epoch in range(cfg.epochs):
        rng.shuffle(order)
        epoch_link = epoch_event = 0.0
        for index in order:
            if time.monotonic() - started > cfg.max_seconds:
                raise TimeoutError("exp067 training walltime exceeded; no usable checkpoint saved")
            sample = train_samples[index]
            if not sample.edge_mask.any() and not sample.event_mask.any():
                continue
            optimiser.zero_grad(set_to_none=True)
            tokens = torch.from_numpy(normalizer.apply_tokens(sample.tokens))
            link, div = model(
                tokens,
                torch.from_numpy(sample.edge_local),
                torch.from_numpy(normalizer.apply_edges(sample.edge_feats)),
                torch.from_numpy(sample.event_local),
                torch.from_numpy(normalizer.apply_events(sample.event_feats)),
            )
            link_loss = masked_bce(
                link, torch.from_numpy(sample.edge_label.astype(np.float32)),
                torch.from_numpy(sample.edge_mask),
            )
            event_loss = masked_bce(
                div, torch.from_numpy(sample.event_label.astype(np.float32)),
                torch.from_numpy(sample.event_mask),
            )
            loss = cfg.link_loss_weight * link_loss + cfg.division_loss_weight * event_loss
            loss.backward()
            optimiser.step()
            epoch_link += float(link_loss.detach())
            epoch_event += float(event_loss.detach())
        scheduler.step()
        history.append(
            {"epoch": epoch, "link_loss": epoch_link, "event_loss": epoch_event,
             "lr": optimiser.param_groups[0]["lr"]}
        )

    payload = checkpoint.build_payload(
        model,
        normalizer,
        seed=cfg.seed,
        train_manifest_sha256=splits.manifest_sha256,
        protocol=splits.protocol,
        train_stems=train_stems,
        holdout_stems=list(splits.holdout),
        counts=counts,
        hyperparams={**asdict(cfg), "config": config.to_dict(),
                     "export_signature": export_signature, "input_sha256": input_hashes},
        division_head_trained=True,
    )
    checkpoint.save(out_path, payload)

    report: dict[str, object] = {
        "checkpoint": str(out_path),
        "protocol": splits.protocol,
        "train_stems": train_stems,
        "inner_val_stems": inner_val,
        "holdout_stems": list(splits.holdout),
        "supervision_counts": counts,
        "n_parameters": model.n_parameters(),
        "emb_channels": channels,
        "history_tail": history[-3:],
        "backbone_provenance": checkpoint.BACKBONE_PROVENANCE,
        "division_head_trained": True,
        "selection_policy": "fixed schedule; no early stopping; no held-out selection",
    }
    if inner_val:
        inner_samples, _ = load_stem_samples(export_dir, label_dir, inner_val, config)
        report["inner_val_supervised"] = evaluate_supervised(model, normalizer, inner_samples)
    holdout_samples, _ = load_stem_samples(export_dir, label_dir, splits.holdout, config)
    report["holdout_supervised_once"] = evaluate_supervised(model, normalizer, holdout_samples)
    report["holdout_supervision_counts"] = supervise.sample_counts(holdout_samples)

    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", required=True)
    parser.add_argument("--label-dir", required=True)
    parser.add_argument("--splits", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--config", default=None)
    parser.add_argument("--report", default=None)
    args = parser.parse_args(argv)

    config = Exp067Config.load(args.config)
    report = train(
        Path(args.export_dir),
        Path(args.label_dir),
        Path(args.splits),
        Path(args.out),
        config,
        Path(args.report) if args.report else None,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

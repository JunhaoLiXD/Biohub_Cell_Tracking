# repro080 admission delta round 1

This delta addresses only F1 and F2 from the initial review.

## F1: approved Tier B exception

The user explicitly approved the offered Tier B exception after the review scope was
stated. The English record is `tier_b_exception.md`, SHA256
`0743cee6c45d32a708bcc7d80cb0526f728c8bfb90ab2bcd1317655c68547064`.
It limits the exception to one byte-verbatim private run and preserves every source,
leakage, budget, runtime-receipt, structural-output, leaderboard, and promotion gate.

## F2: runtime sweep receipt gate

`scripts/audit_repro080_sweep_receipts.py`, SHA256
`0073819ddd247250175883a2da42c3d899a54f73d5ef0c86b2516c39aa250a21`, is the
frozen post-collection gate. It asserts the notebook source hash and requires:

- `ppsweep_selected.json`, `ppsweep_results.csv`, and `run_stats.csv` all exist;
- exactly eight unique held-out TRAIN stems, exactly four `44b6` and four `6bba`;
- exact stem membership and zero overlap with the four TEST stems;
- exactly the 15 preregistered candidates, each with eight samples and exact overrides;
- finite proxy/adjusted-edge metrics;
- independent recomputation of the notebook's 0.0005 proxy-margin and 0.0010
  maximum adjusted-edge-loss selection rule;
- selected label, override dictionary, base proxy, and selected proxy agree;
- exactly four final TEST `run_stats` rows, all tagged with the selected label;
- no repair fallback and no deadline degradation.

It passed on the author's completed public output, selecting `dcsafediv020` with
`DEEPCENTER_SAFE_DIV_THRESHOLD=0.2`. Our collected run must independently pass this
gate and the previously accepted structural submission audit before any later action.

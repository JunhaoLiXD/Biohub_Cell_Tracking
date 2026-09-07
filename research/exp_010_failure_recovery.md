# exp_010 Failure and Recovery

## Failure

`exp_010_train16_deepcenter_div_veto_guarded` failed in the second executed code cell, approximately
10 seconds after notebook startup. Kaggle reported:

```text
RuntimeError: Configuration drift detected:
{"BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD": "missing"}
```

The guard correctly required the changed variable's `0.12` threshold, but the preceding environment
cell set only the veto flag. The later configuration resolver had a `0.12` default, but it had not run
yet. No model inference or hypothesis test occurred, so this is infrastructure failure rather than
negative evidence about the DeepCenter veto.

## Fix

The environment cell now explicitly sets `BIOHUB_DEEPCENTER_SAFE_DIV_THRESHOLD=0.12` before the
configuration guard. Notebook validation also extracts `_EXPECTED_NUMERIC` and `_EXPECTED_TEXT`
keys from configuration-guard cells and rejects a notebook when any key lacks an explicit assignment
in an earlier code cell.

Two regression tests cover rejection of a missing guarded key and acceptance of complete explicit
assignments. The complete local suite passes 23 tests.

## Recovery

`exp_011_train16_deepcenter_div_veto_envfix` preserves the reviewed hypothesis and inference change,
uses a new immutable snapshot, passes the enhanced smoke test, and is running as a private T4 x2
Kaggle experiment. The failed `exp_010` record and log remain intact.

"""Build the v5 zon submission notebook: rerun-aware deadline + view cache outside the output dir.

v5 is a bounded DEPLOYMENT correction on top of the immutable v4 snapshot. The frozen zon
prediction policy, transforms, thresholds, graph writer and every parent inference cell are
untouched; only two hidden-rerun hazards found in the v4 post-run audit are addressed:

  #1  The whole-run watchdog was a hardcoded `signal.alarm(7200)`. A visible run is billed to our
      2.0h GPU reservation so it keeps that ceiling, but the hidden scoring rerun is NOT billed to
      that ledger and can legitimately be slower on a larger hidden dataset. A fixed 2.0h ceiling
      there is the leading hypothesis for the v2 rerun failure ("Your notebook hit an unhandled
      error while rerunning your code"), since v2's visible run already consumed ~2h. v5 keeps 2.0h
      for our own runs and uses a platform-derived 8.5h ceiling when Kaggle sets
      KAGGLE_IS_COMPETITION_RERUN.

  #2  The disk-backed view cache was written under WORKING_DIR (/kaggle/working), so it was both
      captured as kernel output (~4.5 GB for v4) and charged against that 20 GB budget. It measured
      4272 files / 4.48 GB on the public 4-movie workload, which scales straight into the cap on a
      larger hidden rerun. v5 puts it on a scratch root that is not collected as output.

Neither change can alter a single predicted node or edge: the same views are computed, cached and
accumulated in the same order, only somewhere else on disk and under a different time ceiling.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PARENT_NB = ROOT / 'experiments/exp_061_zon_lb_submission_repair_v4/snapshot/source/exp061_zon_submission_repair_v4.ipynb'
PARENT_MODULE = ROOT / 'experiments/exp_061_zon_lb_submission_repair_v4/snapshot/extra_files/exp061_zon_deployment_v4.py'
OUT_MODULE = ROOT / 'scripts/exp061_zon_deployment_v5.py'
OUT_NB = ROOT / '.private/exp061_lb_repair_v5/build/exp061_zon_submission_repair_v5.ipynb'
OUT_CONFIG = ROOT / 'configs/exp_061_zon_lb_submission_repair_v5.yaml'
EXPERIMENT = 'exp_061_zon_lb_submission_repair_v5'
EXPECTED_NB = '39eba1b92c79739b324009a274336672fa098e8f11c4edf1e16c16da6be08290'
EXPECTED_MODULE = '74e3529856694130bf5990b8796db21d9c730b8bcc5f7d09a2fc219f4e23efb8'

VISIBLE_ALARM_SECONDS = 7200        # 2.0h, our reserved GPU budget
RERUN_ALARM_SECONDS = 30600         # 8.5h, under the code-competition platform ceiling

# --- exact cell-2 edits (watchdog arming only; no parent inference line is touched) -------------
CELL2_ALARM_OLD = """_EXP061_WATCHDOG_ARMED = False  # exp061
try:  # exp061
    import signal as _e61sig  # exp061
    if hasattr(_e61sig, 'SIGALRM'):  # exp061
        _e61sig.signal(_e61sig.SIGALRM, _exp061_whole_run_guard)  # exp061
        _e61sig.alarm(7200)  # exp061
        _EXP061_WATCHDOG_ARMED = True  # exp061
except Exception:  # exp061
    _EXP061_WATCHDOG_ARMED = False  # exp061
"""

CELL2_ALARM_NEW = f"""import os as _e61os_rr  # exp061
_EXP061_IS_COMPETITION_RERUN = str(_e61os_rr.environ.get('KAGGLE_IS_COMPETITION_RERUN', '')).strip() not in ('', '0', 'false', 'False')  # exp061
_EXP061_VISIBLE_ALARM_SECONDS = {VISIBLE_ALARM_SECONDS}  # exp061 v5: our own runs stay inside the 2.0h GPU reservation
_EXP061_RERUN_ALARM_SECONDS = {RERUN_ALARM_SECONDS}  # exp061 v5: the hidden rerun is not billed to that ledger
def _exp061_alarm_seconds():  # exp061
    _e61d = _EXP061_RERUN_ALARM_SECONDS if _EXP061_IS_COMPETITION_RERUN else _EXP061_VISIBLE_ALARM_SECONDS  # exp061
    try:  # exp061
        _e61v = float(_e61os_rr.environ.get('BIOHUB_EXP061_HARD_STOP_SECONDS', ''))  # exp061
    except (TypeError, ValueError):  # exp061
        return int(_e61d)  # exp061
    return int(_e61v) if _e61v > 0 else int(_e61d)  # exp061
_EXP061_ALARM_SECONDS = _exp061_alarm_seconds()  # exp061
_EXP061_WATCHDOG_ARMED = False  # exp061
try:  # exp061
    import signal as _e61sig  # exp061
    if hasattr(_e61sig, 'SIGALRM'):  # exp061
        _e61sig.signal(_e61sig.SIGALRM, _exp061_whole_run_guard)  # exp061
        _e61sig.alarm(_EXP061_ALARM_SECONDS)  # exp061
        _EXP061_WATCHDOG_ARMED = True  # exp061
except Exception:  # exp061
    _EXP061_WATCHDOG_ARMED = False  # exp061
"""

CELL2_NOTE_OLD = "'note': 'whole-run 2.0h budget exceeded (top watchdog)'"
CELL2_NOTE_NEW = "'note': 'whole-run budget exceeded (top watchdog)'"
CELL2_RAISE_OLD = "raise KeyboardInterrupt('exp061 whole-run 2.0h budget exceeded')  # exp061"
CELL2_RAISE_NEW = "raise KeyboardInterrupt('exp061 whole-run budget exceeded')  # exp061"

# --- exact module edits -------------------------------------------------------------------------
MODULE_DEADLINE_OLD = "EXP061_HARD_STOP_SECONDS = 2.0 * 3600.0\n"

MODULE_DEADLINE_NEW = f'''import os as _exp061_os  # v5: rerun-aware deadline and scratch-root selection
import tempfile as _exp061_tempfile  # v5


def _exp061_is_competition_rerun():
    """True inside Kaggle's hidden code-competition rerun (Kaggle sets KAGGLE_IS_COMPETITION_RERUN)."""
    raw = str(_exp061_os.environ.get("KAGGLE_IS_COMPETITION_RERUN", "")).strip()
    return raw not in ("", "0", "false", "False")


def _exp061_scratch_root(working_dir):
    """A writable scratch root that Kaggle does NOT collect as kernel output (v5 fix #2).

    Everything under /kaggle/working is captured as output and charged against that 20 GB budget.
    The view cache measured 4272 files / 4.48 GB on the public 4-movie workload, so keeping it in
    WORKING_DIR scales straight into the cap on a larger hidden rerun. Order: explicit override,
    Kaggle's own scratch dir, the platform temp dir, then WORKING_DIR as a last resort so the run
    still completes if nothing else is writable.
    """
    from pathlib import Path as _ScratchPath
    candidates = [_exp061_os.environ.get("BIOHUB_EXP061_SCRATCH_DIR")]
    if _ScratchPath("/kaggle").is_dir():
        candidates.append("/kaggle/temp")
    candidates.append(_exp061_tempfile.gettempdir())
    for candidate in candidates:
        if not candidate:
            continue
        try:
            root = _ScratchPath(candidate)
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".exp061_write_probe"
            probe.write_bytes(b"exp061")
            probe.unlink()
            return root
        except Exception:
            continue
    return _ScratchPath(working_dir)


def _exp061_outside_working_dir(path, working_dir):
    """Telemetry only: report whether the cache escaped the collected output directory."""
    from pathlib import Path as _OutsidePath
    try:
        _OutsidePath(path).resolve().relative_to(_OutsidePath(working_dir).resolve())
        return False
    except Exception:
        return True


# v5 fix #1: a visible run is billed to our 2.0h GPU reservation and keeps the 2.0h ceiling. The
# hidden scoring rerun is NOT billed to that ledger and may legitimately be slower on a larger
# hidden dataset; a fixed 2.0h ceiling there is the leading hypothesis for the v2 rerun failure.
EXP061_VISIBLE_HARD_STOP_SECONDS = {VISIBLE_ALARM_SECONDS}.0
EXP061_RERUN_HARD_STOP_SECONDS = {RERUN_ALARM_SECONDS}.0


def _exp061_hard_stop_seconds():
    """Mirror of the cell-2 arming logic; the notebook asserts the two agree before publishing."""
    default = (EXP061_RERUN_HARD_STOP_SECONDS if _exp061_is_competition_rerun()
               else EXP061_VISIBLE_HARD_STOP_SECONDS)
    try:
        override = float(_exp061_os.environ.get("BIOHUB_EXP061_HARD_STOP_SECONDS", ""))
    except (TypeError, ValueError):
        return float(default)
    return float(override) if override > 0 else float(default)


EXP061_HARD_STOP_SECONDS = _exp061_hard_stop_seconds()
'''

MODULE_VIEWDIR_OLD = '''    view_dir = Path(g["WORKING_DIR"]) / "exp061_viewcache"
    view_dir.mkdir(parents=True, exist_ok=True)
'''

MODULE_VIEWDIR_NEW = '''    # v5 fix #2: the disk-backed view cache must NOT live under WORKING_DIR (see
    # _exp061_scratch_root). Same views, same order, same bytes -- only a different location.
    view_dir = _exp061_scratch_root(g["WORKING_DIR"]) / "exp061_viewcache"
    view_dir.mkdir(parents=True, exist_ok=True)
'''

MODULE_WORKSHEET_OLD = '''        "finalization_reserve_seconds": EXP061_FINALIZATION_RESERVE_SECONDS,
        "hard_stop_seconds": EXP061_HARD_STOP_SECONDS,
'''

MODULE_WORKSHEET_NEW = '''        "finalization_reserve_seconds": EXP061_FINALIZATION_RESERVE_SECONDS,
        "hard_stop_seconds": EXP061_HARD_STOP_SECONDS,
        "is_competition_rerun": _exp061_is_competition_rerun(),
        "view_cache_root": str(view_dir),
        "view_cache_outside_working_dir": _exp061_outside_working_dir(view_dir, g["WORKING_DIR"]),
'''

# --- exact final-cell edit ------------------------------------------------------------------------
# The guard must sit AFTER the parent artifact is unlinked: raising while the parent's own 0.947
# submission.csv is still on disk would leave it to be submitted silently, which is precisely the
# fallback this adapter exists to prevent.
FINAL_GUARD_OLD = '''_zon_telemetry = run_exp061_zon_deployment(globals())
'''

FINAL_GUARD_NEW = '''if int(EXP061_HARD_STOP_SECONDS) != int(_EXP061_ALARM_SECONDS):
    raise RuntimeError("Refusing publication: module deadline disagrees with the armed watchdog")
print("exp061 v5 deadline:", int(_EXP061_ALARM_SECONDS), "s; competition rerun:", _EXP061_IS_COMPETITION_RERUN)
_zon_telemetry = run_exp061_zon_deployment(globals())
'''


def replace_exact(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f'expected one occurrence of {old[:80]!r}, got {text.count(old)}')
    return text.replace(old, new, 1)


def assert_only_exp061_lines_changed(before: str, after: str) -> None:
    """The parent's real inference code carries no `# exp061` marker; none of it may move.

    `# exp061` is the marker the whole exp061 builder chain uses for its strippable injections, so
    dropping every line carrying it leaves exactly the parent's own code on both sides.
    """
    keep_before = [line for line in before.splitlines() if '# exp061' not in line]
    keep_after = [line for line in after.splitlines() if '# exp061' not in line]
    if keep_before != keep_after:
        raise RuntimeError('v5 cell-2 edit touched a non-exp061 line')


def build() -> None:
    parent_bytes = PARENT_NB.read_bytes()
    module_bytes = PARENT_MODULE.read_bytes()
    if hashlib.sha256(parent_bytes).hexdigest() != EXPECTED_NB:
        raise RuntimeError('v4 immutable notebook identity changed')
    if hashlib.sha256(module_bytes).hexdigest() != EXPECTED_MODULE:
        raise RuntimeError('v4 immutable deployment module identity changed')
    parent_nb = json.loads(parent_bytes.decode('utf-8'))
    nb = copy.deepcopy(parent_nb)

    module = module_bytes.decode('utf-8')
    module = replace_exact(module, 'EXP061_EXPERIMENT_ID = "exp_061_zon_lb_submission_repair_v4"',
                           'EXP061_EXPERIMENT_ID = "exp_061_zon_lb_submission_repair_v5"')
    module = replace_exact(module, 'EXP061_VALIDATION_PROTOCOL = "exp061_zon_only_deployment_v4"',
                           'EXP061_VALIDATION_PROTOCOL = "exp061_zon_only_deployment_v5"')
    module = replace_exact(module, MODULE_DEADLINE_OLD, MODULE_DEADLINE_NEW)
    module = replace_exact(module, MODULE_VIEWDIR_OLD, MODULE_VIEWDIR_NEW)
    module = replace_exact(module, MODULE_WORKSHEET_OLD, MODULE_WORKSHEET_NEW)
    compile(module, 'exp061_zon_deployment_v5.py', 'exec')

    cell2_before = ''.join(parent_nb['cells'][2]['source'])
    cell2 = replace_exact(cell2_before, CELL2_ALARM_OLD, CELL2_ALARM_NEW)
    cell2 = replace_exact(cell2, CELL2_NOTE_OLD, CELL2_NOTE_NEW)
    cell2 = replace_exact(cell2, CELL2_RAISE_OLD, CELL2_RAISE_NEW)
    assert_only_exp061_lines_changed(cell2_before, cell2)
    if 'alarm(7200)' in cell2:
        raise RuntimeError('hardcoded 7200s alarm survived the v5 edit')
    compile(cell2, 'v5_cell_2', 'exec')

    final = ''.join(parent_nb['cells'][4]['source'])
    final = replace_exact(final, FINAL_GUARD_OLD, FINAL_GUARD_NEW)
    compile(final, 'v5_final_cell', 'exec')

    nb['cells'][2]['source'] = cell2.splitlines(True)
    nb['cells'][3]['source'] = module.splitlines(True)
    nb['cells'][4]['source'] = final.splitlines(True)
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            cell['outputs'] = []
            cell['execution_count'] = None
    if nb['cells'][:2] != parent_nb['cells'][:2]:
        raise RuntimeError('v4 parent markdown/setup cells changed')

    OUT_NB.parent.mkdir(parents=True, exist_ok=True)
    OUT_MODULE.write_text(module, encoding='utf-8', newline='\n')
    OUT_NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding='utf-8', newline='\n')

    config = yaml.safe_load((ROOT / 'configs/exp_061_zon_lb_submission_repair_v4.yaml').read_text(encoding='utf-8'))
    config['experiment_id'] = EXPERIMENT
    config['parent'] = 'exp_061_zon_lb_submission_repair_v4'
    config['source_notebook'] = OUT_NB.relative_to(ROOT).as_posix()
    config['hypothesis'] = (
        'The v4 hidden-rerun outcome is gated by deployment-scale limits, not by the zon prediction policy: '
        'a fixed 2.0h watchdog and a 4.48 GB view cache inside the collected output directory both fail on a '
        'sufficiently larger hidden dataset. Removing both limits without touching any predicted value lets the '
        'rerun finish. The exact v2/v4 hidden failure cause remains unproven.')
    config['change'] = {
        'component': 'zon_only_submission_transport_v5',
        'from': 'v4: hardcoded signal.alarm(7200) and view cache under WORKING_DIR',
        'to': 'rerun-aware deadline (2.0h visible / 8.5h hidden rerun) and view cache on a non-output scratch root',
        'variables_changed': 'deployment resource limits and cache location only; frozen zon prediction policy'}
    config['validation']['protocol'] = 'exp061_zon_only_deployment_v5'
    config['validation']['warning'] = (
        'Deployment integrity only, not a quality metric. The v2 and v4 hidden tracebacks are unavailable, so the '
        'scale hypothesis is not proven. The watchdog still covers parent inference, zon replay, final audit, '
        'staging and publication. A separate authorization is required for any leaderboard submission.')
    config['substrate_note'] = (
        'Unchanged v4 parent inference cells and frozen zon prediction/graph-writer policy. The only behavioral '
        'changes are the rerun-aware whole-run deadline and moving the view cache off the collected output path; '
        'both are resource-placement changes that cannot alter a predicted node or edge.')
    config['provenance']['builder'] = 'scripts/build_exp061_zon_submission_repair_v5.py'
    config['provenance']['appended_module'] = 'scripts/exp061_zon_deployment_v5.py'
    config['provenance']['source_parent'] = 'exp_061_zon_lb_submission_repair_v4 (launched, kernel COMPLETE, LB submission 56481730)'
    config['authorization']['scope'] = (
        'The user asked for a corrected version to be built and pushed to Kaggle immediately, as a fallback in case '
        'the v4 leaderboard submission (56481730) fails again. That is a one-time user waiver of the Codex admission '
        'gate for this bounded deployment fix, NOT a Codex PASS. It authorizes one tracked kernel run after snapshot '
        'smoke and budget reservation. It does not authorize a leaderboard submission.')
    config['provenance']['expected_v4_notebook_sha256'] = EXPECTED_NB
    config['provenance']['expected_v4_module_sha256'] = EXPECTED_MODULE
    config['provenance']['generated_zon_deployment_sha256'] = hashlib.sha256(OUT_MODULE.read_bytes()).hexdigest()
    config['provenance'].pop('expected_v3_notebook_sha256', None)
    config['provenance'].pop('expected_v3_module_sha256', None)
    config['provenance']['strategy_amendment'] = 'experiments/exp_061_zon_lb_submission_repair_v5/strategy_amendment_v1.md'
    config['kaggle']['slug'] = 'biohub-exp061-zon-deploy-v5'
    config['kaggle']['title'] = 'biohub-exp061-zon-deploy-v5'
    config['kaggle']['extra_files'] = [
        'scripts/build_exp061_zon_submission_repair_v5.py',
        'scripts/exp061_zon_deployment_v5.py',
        'scripts/validate_exp061_zon_deployment_v5.py',
        PARENT_NB.relative_to(ROOT).as_posix(),
        PARENT_MODULE.relative_to(ROOT).as_posix(),
    ]
    config['local']['smoke_test'] = ['{python}', 'scripts/validate_exp061_zon_deployment_v5.py', '{source_notebook}']
    OUT_CONFIG.write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')

    receipt = {
        'parent_notebook_sha256': EXPECTED_NB,
        'parent_module_sha256': EXPECTED_MODULE,
        'module_sha256': hashlib.sha256(OUT_MODULE.read_bytes()).hexdigest(),
        'notebook_sha256': hashlib.sha256(OUT_NB.read_bytes()).hexdigest(),
        'visible_alarm_seconds': VISIBLE_ALARM_SECONDS,
        'rerun_alarm_seconds': RERUN_ALARM_SECONDS,
        'view_cache_off_working_dir': True,
        'parent_inference_lines_unchanged': True,
    }
    (OUT_NB.parent / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    build()

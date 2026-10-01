# repro081 admission delta round 1

This delta addresses only R081-TEST-001, R081-BUDGET-001, and R081-PARENT-001.

## R081-TEST-001

`admission_test_receipts.json` records exact commands, exit codes, bounded stdout,
snapshot/upstream hashes, and public fixture hashes. All four deterministic commands
returned zero:

1. immutable source reconstruction and syntax smoke;
2. runtime receipt positive test plus three negative mutations;
3. sweep receipt fixture audit;
4. structural submission fixture audit.

The negative mutations disable the validator, erase effective overrides, and alter
the final artifact hash; each is rejected.

## R081-BUDGET-001

The controller reserved 3.0 GPU hours for repro081. `GPU_BUDGET.json` now records:

- remaining before outstanding reservations: 24.281728888228336 hours;
- diag078 reservation: 1.0 hour;
- repro081 reservation: 3.0 hours;
- remaining after all reservations: 20.281728888228336 hours.

The six-hour protected reserve remains intact.

## R081-PARENT-001

The repro081 experiment record now contains an explicit `authorization` object. It
records the user-approved Tier B exception and the user's direction to continue with
repro081 after being told that repro080 was unlaunched and lacked only effective
runtime receipts. It explicitly authorizes repro081 to supersede that unlaunched
parent while retaining its closed findings. Scope remains one private run, no retry,
no leaderboard submission.

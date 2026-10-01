# diag073 cache-transport repair

Local repair is complete and smoke-tested. No remote launch or leaderboard
submission has occurred.

Root cause: exp065 preserved the eight expected validator `.geff` directory
trees but did not emit `cache_key.txt`; the inherited cache consumer required
that nonexistent file. Its cache-hit copy path also used file-only `copy2` for
GEFF directories.

The repair authenticates every GEFF tree by recursive SHA256 and uses
`copytree`. The smoke test verifies all eight hashes, a successful directory
copy, a tamper negative control, fork protection, and primary-only execution.
Only notebook cell 7 differs from the immutable diag072 snapshot.

The immutable snapshot was created and its targeted smoke passed. Admission
round 1 returned REVISE F1 because a pre-existing destination could be reused.
The single permitted delta now rejects any pre-existing destination and verifies
the copied-tree digest; its positive and negative controls pass.

The delta review returned BLOCK solely because its read-only command runner
failed environment setup three times before accessing any file. It made no
substantive implementation finding. Tier B permits only one delta review, so the
formal result is NO_CONSENSUS. No GPU was reserved and no remote launch occurred.
Do not retry review or launch without a new explicit user decision. LB
submissions remain forbidden.

## Remote result after user waiver

The user later authorized one waiver launch. Kaggle version 1 terminated in
`ERROR` after approximately 12 seconds, in notebook cell 4, before cache
transport or scientific evaluation. The immediate exception was:

`FileNotFoundError: Could not find the required model artifact. Expected slug: biohub-tracking-support-pack-50ep-v1`

This was a packaging failure. The frozen config omitted `dataset_sources`,
`competition_sources`, `kernel_sources`, and `docker_image`. The prebuilt
`kaggle_kernel/kernel-metadata.json` happened to contain the required four model
datasets, competition source, exp065 kernel source, and pinned image. The launch
path staged `kaggle_kernel_retry_001` from the frozen config, producing empty
source arrays; Kaggle received that generated metadata. No primary receipt or
scientific result exists. Do not relaunch diag073. A successor must pin all
remote sources in its tracked config and smoke-test the generated metadata.

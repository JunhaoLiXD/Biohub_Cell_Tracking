# diag075 local packaging rejection

No remote launch or GPU reservation occurred. The first local smoke found that
the configured `.private/current` working copy predated the final diag073
destination-integrity correction. The immutable diag075 snapshot is retained as
failed local evidence and must not be launched. Successor diag076 instead names
the final immutable diag073 snapshot as its source.

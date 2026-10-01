# diag076 remote result — terminal mount-path failure

Kaggle version 1 terminated in `ERROR` after approximately 2631 seconds. The
tracked metadata repair worked: competition and model inputs were mounted, all
four TEST movies completed, and the run reached the validator cache gate.

The eight frozen validator GEFF trees were then all absent at the notebook's
legacy path:

`/kaggle/input/biohub-exp065-pruning-sweep/tracking_repo/predictions/unknown/unet_transformer_val/split_0`

The current Kaggle runtime uses namespaced input mounts, as demonstrated in the
same log by competition paths under `/kaggle/input/competitions/...` and dataset
paths under `/kaggle/input/datasets/<owner>/...`. The attached exp065 kernel
output is correspondingly expected under `/kaggle/input/kernels/lingxd/biohub-exp065-pruning-sweep/...`,
not the legacy flat path hard-coded in the inherited notebook. The public exp065
output file listing confirms that the validator GEFF content exists remotely.

The fail-closed assertion worked as designed:

`AssertionError: diag072: frozen cache invalid; inference fallback prohibited`

No primary receipt or scientific result exists. Do not relaunch diag076. Any
successor must resolve and authenticate the actual namespaced kernel-source root
before TEST inference, then consume the same immutable eight-tree hashes. No LB
submission or confirmatory work is authorized.

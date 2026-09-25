# exp_063 Codex admission review — VERDICT: BLOCK

Reviewer: Codex `gpt-6-astra`, effort low, read-only, 2026-09-24. Target: the frozen snapshot
`fb2b1cd4d9612d333eb2e8ad6c0106646ac2429c05ccfce5997179135a228734` + `PRE_LAUNCH_AUDIT.md`.

**This is a genuine BLOCK, not a tool-access block.** Codex independently verified the snapshot and
archive hashes, then found real defects by static inspection.

## Claude Code's independent verification of the two headline findings

Both were checked against the frozen snapshot before being accepted. **Both are correct.**

1. **DivNet is structurally inoperative — CONFIRMED.** `DivNetMitosisClassifier.b1` is
   `_DivNetConvBlock(1, 16)`, so its first `Conv3d` takes `in_channels=1` and needs a 5-D
   `(N,1,D,H,W)` input (cell 11 line 1672). But line 1751 builds `padded` as **4-D**
   `(4, 2*z_pad, 2*xy_pad, 2*xy_pad)` and line 1759 applies `.unsqueeze(0).unsqueeze(0)`, giving a
   **6-D** tensor. `Conv3d` rejects it; line 1764 swallows the exception and returns `None`; the
   veto at line 1617 fires only `if _div_prob is not None`. **The DivNet gate can never veto
   anything.** (One `unsqueeze` would not fix it either — that gives 4 channels into `in_channels=1`.)
2. **"It preserves our tight55" — CONFIRMED FALSE.** Cell 11 lines 3–22 define
   `DENSITY_GROUP_OVERRIDES` with `tight_um` **7.25 (low) / 6.5 (middle) / 5.5 (high)**, selected by
   `determine_density_group` on measured `avg_per_frame` (<120 low, <400 middle, else high).
   `BIOHUB_MOTION_RELINK_TIGHT_UM = "5.5"` is only a default that these overrides replace. Our
   tight55 survives **only on high-density movies**.

   This also means **proposal v2 was wrong to say the recon's discrete-group table "does not match
   this notebook"** — it matches exactly. The notebook carries **both** the discrete table and the
   continuous gap-density adaptation.

   Claude Code made the same class of error twice: in v1 by reading marker counts as behaviour, and
   in v2 by reading an environment assignment as effective behaviour. Codex caught both.

## Additional accepted findings

- `ground_truth_accessed: False` is a **hardcoded constant** written at cell 7 line 673, *before*
  dynamic patching and prediction. `PRE_LAUNCH_AUDIT.md` item 4 cited it as evidence. That was
  wrong; it is an assertion, not an observed access record.
- Audit item 10 ("subprocess only for sharded inference") is **false** — cell 7 lines 291–315 invoke
  pip. Item 8's "no writes outside the working dir" is therefore also unsupported.
- The gate field `exp063_repro_integrity_passed` is never emitted by the notebook, and the smoke
  command omits `--require-metrics-contract`. The collection contract is incomplete.
- `expected_gpu_hours` is an accounting figure, not an enforceable termination mechanism.

## One correction to the review

Codex implies the unrestricted-pickle load is unavoidable under the verbatim route. It is not:
`load_divnet_mitosis_model()` returns early at **line 1691** when `DIVNET_VERIFY` is falsey, and it
also degrades cleanly to "geometric baseline mode" (line 1719) when none of the four candidate paths
exist. So **simply not mounting `giorgosi/biohub-divnet-v2` removes the pickle surface without
editing a single line of the notebook.** And because the gate is provably dead, doing so should
leave predictions byte-identical — a claim that is itself testable.

---

**Do not launch this snapshot under the submitted admission record.** A bounded whole-pipeline reproduction remains defensible. This audit does not establish what the pipeline actually executes, and several of its supporting claims are false.

I independently verified that the archive and snapshot both hash to `fb2b1cd4d9612d333eb2e8ad6c0106646ac2429c05ccfce5997179135a228734`; the snapshot config also matches the working config. Findings below are from static inspection, not GPU execution. Notebook references use **zero-based cell numbers and one-based source lines** in the [frozen notebook](E:/Project/Biohub_CellTracking/experiments/exp_063_public_0951_pipeline_repro/snapshot/source/biohub-0-951-sota-deepcenter-fast-ilp-19m.ipynb).

1. **DivNet is broken and silently bypasses verification.**

   Cell 11, lines 1751–1759 constructs `padded` with shape `(4,16,32,32)`, then applies two `unsqueeze(0)` operations, producing **`(1,1,4,16,32,32)`**. The model immediately feeds this six-dimensional tensor into `Conv3d` at lines 1659 and 1684. `Conv3d` accepts four-dimensional unbatched or five-dimensional batched input. [PyTorch documentation](https://docs.pytorch.org/docs/2.14/generated/torch.nn.Conv3d.html)

   Lines 1764–1765 swallow the exception and return `None`. Lines 1617–1618 veto only when the probability **is not `None`**. Consequently, this inference path cannot perform the advertised DivNet verification.

   Loading is also permissive: lines 1709–1719 use `weights_only=False`, ignore missing/unexpected keys with `strict=False`, and fall back to geometry after loading failures. “Loaded successfully” would not establish that the intended trained model was loaded.

   Verbatim reproduction can deliberately reproduce an upstream defect. It cannot honestly be described as testing five functioning mechanisms when one is structurally inoperative.

2. **The claim that the pipeline preserves tight55 is false for the executed relinker.**

   [Proposal v2:46](E:/Project/Biohub_CellTracking/docs/research/exp063_next_step_proposal_v2.md:46) and [config:20](E:/Project/Biohub_CellTracking/configs/exp_063_public_0951_pipeline_repro.yaml:20) mistake an environment assignment for effective behavior.

   Cell 11, lines 3–35 defines **discrete density groups**, selected by average detected nodes per occupied frame:

   | Group | Density | Tight distance | Relaxed distance | Learned bonus |
   |---|---:|---:|---:|---:|
   | Low | `<120` | 7.25 | 11.0 | 3.0 |
   | Middle | `<400` | 6.5 | 9.0 | 6.0 |
   | High | `≥400` | 5.5 | 10.0 | 1.0 |

   Lines 1513–1521 pass these values directly into `motion_relink_edges`. Only the high-density group retains tight55. The notebook contains **both** discrete relinking overrides and continuous gap-density adaptation. V2’s assertion that the discrete-table description does not match this notebook is wrong.

   This is prediction-derived branching, not demonstrated leakage. It nevertheless invalidates the submitted effective-change description.

3. **The minimum audit is only partially discharged.**

   The actual round-1 requirements are at [challenge:53](E:/Project/Biohub_CellTracking/docs/research/exp063_codex_challenge_v1.md:53).

   | Requirement | Finding |
   |---|---|
   | Frozen notebook and acquisition metadata | **Substantially discharged:** hash independently verified; source slug and acquisition date archived. Exact upstream kernel version is not recorded in the supplied metadata. |
   | Environment, dataset versions, checkpoint hashes | **Partial:** Docker digest is pinned. Cell 7 genuinely checks three checkpoint hashes and 13 support Python files. Dataset slugs are not dataset-version pins; offline package versions/hashes and DivNet identity remain unbound. |
   | Executed imported/unpacked code | **Not discharged:** cell 7 copies/extracts the support repository and installs packages; cell 9 dynamically patches the predictor. The audit provides no trace through that materialized execution path. |
   | Prediction paths and fallbacks | **Not discharged:** TTA can revert to four-way inference (cell 9:53–57); the rank patch can silently remain unapplied (278–284); DivNet can silently disappear. |
   | GT use and specimen branching | **Partial:** dynamic test discovery is real. Absence of four names or `solution.csv` does not clear imported code or weights. The density branch was missed. |
   | Output schema and graph integrity | **Partial:** cell 13 checks schema, dynamic coverage, endpoints, next-frame edges and degree limits. Its checks do not establish unique node IDs, finite coordinates, integral values before casts, or upper image/time bounds. The proposed collection gate omits these independent checks. |
   | Hidden rerun and resources | **Open:** dynamic discovery helps, but there is no demonstrated clean-environment compatibility or bounded memory/disk/runtime behavior. |

   Two audit claims are specifically untenable:

   - **“Subprocess only for sharded inference” is false:** cell 7:291–315 invokes pip. “Zero writes outside working” is unsupported when package installation is allowed.
   - **`ground_truth_accessed: False` is a constant**, written in cell 7:673 **before dynamic patching and prediction**. It is not an observed access record.

   The guard report also contains stale hardcoded configuration: cell 13 reports detection threshold `0.96875`, disappearance weight `1.5`, and gap distance `5.8`; the environment sets `0.965`, `2`, and `5.0`. Its metadata cannot substitute for effective-configuration evidence.

4. **“Run verbatim and record DivNet provenance open” is unacceptable here.**

   [Audit:35](E:/Project/Biohub_CellTracking/experiments/exp_063_public_0951_pipeline_repro/PRE_LAUNCH_AUDIT.md:35) narrows permitted provenance to whether public test labels exist. That does not establish training inputs, permitted data use, or checkpoint integrity.

   There is also an execution issue: the unverified checkpoint is deserialized with `weights_only=False`. That invokes unrestricted pickle loading; disabled internet does not establish safe checkpoint execution. [PyTorch documentation](https://docs.pytorch.org/docs/2.14/generated/torch.load.html)

   **For the submitted verbatim route, unresolved DivNet provenance blocks admission.** Establish and freeze its provenance and bytes, or propose a separately reviewed variant that disables loading. Disabling verification removes this model from execution; it does not retrospectively establish its provenance or clear the remaining audit gaps. Its small claimed metric weight is irrelevant to admission.

5. **The budget fits financially but is not an enforced ceiling.**

   [GPU_BUDGET.json:4](E:/Project/Biohub_CellTracking/GPU_BUDGET.json:4) records **16.872382 hours**, including **6 protected hours**: discretionary capacity is **10.872382 hours**. A 2-hour allocation fits.

   However, [config:91](E:/Project/Biohub_CellTracking/configs/exp_063_public_0951_pipeline_repro.yaml:91) supplies `expected_gpu_hours`, not a termination mechanism. The notebook’s shard wait can run indefinitely while workers remain alive; its 30-second timeout applies only to cleanup after another worker fails.

   Define an enforceable cumulative limit, accounting units, cancellation mechanism, and the remaining allowance required before any retry. Clarify whether “two runs” includes repair runs and how hidden reruns are counted or excluded from charged GPU time. “Exactly one submission” and “one hidden-rerun retry” also need explicit reconciliation.

   The comparator `max(0.947, exp_062 k2)` and equal/below stop rules are sound. Preserve v2’s requirement to resolve k2 before submission. Compare candidate bytes against **both** known outputs, not only `d3453380…`. The local ledger now records submission **56530197**; v2’s “zero used today” is stale. Every submission still requires the three-per-New-York-day remote check.

6. **The collection contract is incomplete.**

   The config names `exp063_repro_integrity_passed`, but the notebook never emits that field or `metrics.json`. Specify and review the external collection adapter if verbatimness is retained.

   The configured smoke omits `--require-metrics-contract`; [validator:514](E:/Project/Biohub_CellTracking/experiment_controller/core.py:514) shows even general syntax parsing is conditional on that flag. This smoke cannot establish DivNet execution, successful dynamic patches, or hidden-rerun readiness.

**Blocking defect:** admission presently relies on unresolved executable-weight provenance and a materially inaccurate execution audit. Correct the effective-pipeline description, complete the missing evidence, and establish enforceable resource and collection contracts before reconsideration. No files were changed.

VERDICT: BLOCK

# Colab Operator Runbook

## Current Gate

The live smoke gate has passed three times, each from an exact commit in two
fresh NVIDIA L4 runtimes: a822b9a0 on 21 September 2026 (the first tested
profile, [decision D-20260922-12](DECISIONS.md#d-20260922-12---freeze-the-tested-colab-environment-profile-from-run-a-and-run-b)),
0cc9ad77 on 22 September (evidence only, including the representation-mode
measurements in [REPRESENTATION_MODES.md](REPRESENTATION_MODES.md)) and
e7d45fc8 on 4 October 2026 under budget pool A, in the repo_compatible mode of
D-20261004-13 and after the Phase 4 code. The tested profile
`configs/environments/colab_tested.yaml` with `requirements/colab-core.lock.txt`
is re-frozen from the e7d45fc8 pass with `compute_budget_approved: true` under
[decision D-20261004-18](DECISIONS.md#d-20261004-18---re-freeze-the-tested-colab-profile-from-the-e7d45fc8-gate-pass-with-the-compute-budget-approved),
so the final stages (feature generation, training, evaluation) are open from
any commit that descends from e7d45fc8 without a change to `src/rag_cad` or
`scripts/bootstrap_colab.py`; such a change invalidates the profile until the
gate is rerun. For the smoke gate, the standing instruction applies: Daniel
Song setting the two flags and running the runner from a named commit is the
authorisation for that commit. No code changes may be made or pushed from
Colab. The candidate profile remains for further bounded smoke or conformance
work; final stages and released-test runs need their own authorisation.

## Before Phase 1B

1. Review the Phase 1A diff and passing CPU/CI checks. Merge using a merge commit
   to retain the pinned upstream ancestor. Record the exact resulting SHA.
2. Resolve and review the candidate Linux dependency lock, candidate GPU/Python/
   package fingerprint, separate weights/tokenizer and remote-code revisions,
   explicit native attention, temporary smoke representation,
   segmenter resource revision/hash, and numeric tolerances. The provisional
   `requirements/colab-core.in` is not an approved lock. Its generator is absent
   intentionally because Phase 1B uses a fake generator.
3. Review the Ubuntu-generated `requirements/colab-core.candidate.lock.txt` and
   its CPU install/test and storage evidence. This is not a Windows dev lock or
   evidence that Colab/real-model execution has passed.
4. Explicitly approve the overall candidate before execution. Smoke/conformance
   may discover null Python patch, GPU name/VRAM, CUDA, and driver fields.
   Measurements must be complete; CUDA must be available, VRAM strictly greater
   than 8 GiB, and Python must be 3.13.x (D-20260921-11). Non-null expectations must match.
   Packages, lock, model/code pins, dtype, attention and segmenter are never
   inferred or relaxed. Failed measurement validation records failure and stops
   before models. Success records the measured fingerprint without editing the
   candidate. Final stages require tested status, no unknowns, and exact match.
   `lock_sha256` identifies the committed lock.
   `proposal_only` must cease to be true only after explicit approval. Network,
   remote-code execution, licence use, and compute budget need their own review;
   changing one approval flag does not grant the others. `segmenter` is the
   canonical JSON SHA-256 of `segmenter_resource`, including
   its immutable NLTK-data revision and zip hash. No NLTK resource download occurs
   at import time. Expected versions include torch, transformers, numpy, nltk,
   scikit-learn, faiss-cpu, huggingface-hub, einops, and sentencepiece. The actual
   CUDA build/driver and GPU memory must be measured, not guessed from a T4 label.
5. Drive root and operator are confirmed as
   `/content/drive/MyDrive/COMPSCI764_RAG_CAD/artefacts` and Daniel Song.
   Capacity, sharing, and live I/O still need manual confirmation.
6. Record the SHA-256 of `scripts/bootstrap_colab.py` from the reviewed commit.
   Supply the private repository read-only token in Colab Secrets as
   `GH_READ_TOKEN`. No token belongs in an input cell, Git URL, or saved output.
   The researcher reports this secret is prepared. The corrective pass never
   accesses it. Bootstrap and installation now require explicit network permission
   before any secret retrieval or subprocess download.

## Notebook Sequence

The output-cleared runner accepts an exact commit, bootstrap hash, approved
profile/lock paths, run ID, stage, and optional input manifests. The clone cell
uses the token only for git clone, never an API download of the bootstrap.
It clears the temporary environment and removes askpass before verifying the
exact checkout and clean remote. It then hashes and executes the local helper.

Run a prefilled copy with Runtime > Run all. The cells execute in order and
every later cell refuses to run after an earlier failure, so a failed run stops
at its failing cell. The last cell prints one compact JSON summary of the run
for the record: the non-secret inputs, the preflight report, the progress steps
and any sanitised failure record, each top-level JSON report of the stage output
with training histories, locked-package lists and tensor inspections dropped and
long lists or strings truncated, an inventory of the stage directory by file
count and bytes, the publication result and the elapsed time. It reads only the
local workspace, never Drive or a secret, and can be run alone after a failure.
The remaining manual steps are Colab's own prompts: granting the notebook access
to the GH_READ_TOKEN secret and authorising the Drive mount.

Installation, CPU tests, and preflight run before the explicit Drive mount cell.
The bootstrap creates a fresh isolated virtual environment outside the checkout
(`/content/rag-cad-venv`) without pip, because Colab's Python build lacks
`ensurepip`; Colab's system pip then installs the committed candidate lock
(which pins pip and setuptools) into that environment with `pip --python`, and
the environment's own interpreter installs the project and returns as the
project interpreter. `pip check`, the CPU tests, preflight and every later
project CLI command use that interpreter, never Colab's system Python, whose
preinstalled packages conflict with each other and with the lock
(D-20260921-10). Scientific commands always run in new Python subprocesses, so
the notebook kernel never holds imported ML binaries across installation. A
preflight failure blocks mounting and execution. Work happens under the
temporary workspace.

Failed project CLI commands still print no output. Instead the smoke command
records fixed-vocabulary progress steps in `smoke_progress.json` under the
workspace as each stage completes, and a refused command writes
`last_failure.json` holding only the command labels and the exception class
name. The smoke cell prints both files after the stage, whether it passed or
failed, so a failure can be located without exposing command output, paths or
exception text.

Drive mounts only for required input restoration, then unmounts in finally before
model loading. Run B uses a local verified input directory and separate receipt
(`--destination` and `--receipt`), never an active Drive input. The model cell
refuses execution while Drive is mounted. Publication remounts only for copying
and verification and unmounts in finally. Jina weight files cannot be published.

For first acquisition, explicitly approve network use. Only four named CAD files
are downloaded at immutable revisions and verified before parsing/loading.
The pinned NLTK resource is also hash-checked and safely extracted. Alternatively,
restore an approved source bundle containing `upstream/` and `nltk_data/` into
the local `inputs/` directory. Existing mismatched/partial inputs are not silently
overwritten. Use a fresh run/destination after investigating failures.

The Jina loader accepts separate model and code revisions plus `--model-bundle`
under the active workspace. Only five named model/tokenizer files and ten named
code files are acquired when both execution and download permissions allow it;
there is no full-snapshot download. Existing bundles must verify their revision
and file-hash manifest. Without network permission, a missing bundle fails closed.
The original configs are retained; derived configs remove remote repository
prefixes from `auto_map` and remove `_name_or_path`. Model and internal tokenizer
lookups therefore use the same verified local directory. Before loading, the ten
verified code files are also staged into transformers' dynamic-module cache
directory for the bundle, because transformers copies only one level of relative
imports from a local directory and the pinned code has two; without staging the
load fails with FileNotFoundError at the model-loading step. Loading/inference uses
local-only settings and a network-denial context, with native attention and
float32 fixed explicitly. This is defence in depth, not a sandbox: the exact code
still requires review and explicit remote-code permission before execution.

Every actual active source, resource, model bundle, restore destination, and
output must stay inside the local workspace; Drive and linked paths are rejected.
Drive manifest reads and publication destinations are deliberate storage
exceptions. Neither an innocuous `--workspace` argument nor a symlink can make an
active Drive path acceptable.

Run A checks deterministic three-row features, released-checkpoint probabilities,
one synthetic-label MLP epoch/save/reload, tiny CPU FAISS serialization/retrieval,
and fake-generator checkpoint-swap invariants using two tiny, explicitly synthetic
checkpoint-backed CADScorer instances. The smoke MLP is not a primary condition.
Run A also encodes the same three sentences in both representation modes
(`repo_compatible` and `paper_exact`) and records, as `representation_modes`,
each mode's shape, finiteness, determinism, runtime, released-checkpoint
probabilities and removal decisions, whether the isolated blocks are identical
and the largest contextual difference. This is the evidence for the
D-20260921-05 representation decision; the report selects no mode, and the
progress step `modes_compared` marks it.
Reports include provenance, tolerances, checkpoint metadata/tensor inspection,
maximum token length, RAM and disk snapshots, stage timings, output bytes, and
peak GPU memory. RAM/disk snapshots are not peak-memory or peak-disk claims.
Three-row throughput is not a full-dataset runtime estimate.

Run A stores `source_manifest.json`, `preflight.json`, its report, predictions,
features, checkpoints, and real model-bundle manifest inside the stage directory
that is published. Run B also retains current source validation and references
the parent artefact manifest hash. Source validation is regenerated and preserved
even when inputs were restored rather than downloaded. Publication hashes cover
the entire stage, including these audit records.

Publish after the stage succeeds. The immutable artefact protocol writes the
success marker last and verifies payload/member hashes. Retain the published
Run A manifest and source bundles. Delete the runtime yourself; no local test
can demonstrate that action.

Start Run B in a fresh hosted runtime with the same reviewed commit/environment.
Restore the verified Run A bundle and compare its saved checkpoint predictions.
The command rejects the same runtime identity and mismatched provenance.
Run B must reproduce Run A's observed environment, even when both began with
unknown candidate runtime fields.
Publish Run B evidence under a new run ID. Neither command automatically changes
a candidate to tested. Only after all Run A/B checks, researcher review, and a
committed resulting lock/profile may `status: tested` be used.

The `released-test` stage (`STAGE = "released-test"`) runs
`conformance released-test` from the same runner. It validates the release,
prepares the segmenter resource and the Jina bundle exactly as Run A does,
scores `testing_data_original` with the released checkpoint under both
representation modes, and writes `released_test_evaluation.json`,
`predictions.jsonl`, `preflight.json` and `source_manifest.json` into the
stage output, which Cell 7 publishes under the `conformance` stage on Drive.
`RELEASED_TEST_RECORDS` in the input cell limits the run to the first N records
in the upstream sorted-path order (0 means every record). Both modes are built
from one set of encoder passes, and per-domain metrics use the upstream
definition of a domain: the first directory under the extracted test folder
(banking, slack, travel). The ten-record pilot of 23 September 2026 took
9 minutes and 0.07 units (39.5 ms per encoder pass), and the full run the
same day (UTC) scored all 389 records with 19,941 encoder passes in 13.7
minutes of encoding (41.3 ms per pass); both are recorded in
[PROGRESS.md](PROGRESS.md). The stage uses the candidate profile, but the
standing smoke instruction does not cover
it: each released-test run needs its own explicit authorisation and, for the
full run, an approved budget. Over-length records (more than 8,192 tokens) are
skipped and listed rather than silently truncated as the upstream builder
would. Its progress steps are released_test_extracted, released_test_encoded,
released_test_scored and released_test_report_written. The report selects no
representation mode; see [REPRESENTATION_MODES.md](REPRESENTATION_MODES.md).

`m0 run` is the Phase 4 baseline stage and the first final stage: behind the
`train` gate (tested profile, approved compute budget, unchanged tested code,
CUDA runtime) it adapts the pinned release, assigns the split with every D0
record pinned to train and every released test record pinned to test, records
the released train/test leakage report without enforcing it, builds the
m0_base training features and the common test features, trains one head per
declared seed under the fixed recipe, evaluates every seed and the released
checkpoint on the same test features, and writes `phase4_report.json` with
per-seed checkpoint directories under `models/m0_base/`. `m0 fake-run` is its
CPU twin on synthetic identities. Its notebook stage is `STAGE = "m0"` under
budget pool B: the preflight runs at the `train` stage, the stage label is
`phase4_m0`, and Cell 7 publishes under the `phase4` stage on Drive.
The first m0 run (4 October 2026, run ID 20261004T101405Z_d40b6a6a_m0_8c0933ce,
commit d40b6a6a) took 1 hour 12 minutes connected and 2.17 units on an L4 at a
displayed rate of 1.54 units per hour: 66 minutes of stage time, almost all of
it the two feature builds (24,665 training and 9,776 test rows), with each
30-epoch head training in about 35 s. Pool B holds 4 hours and 8 units, so one
further run of this size fits; later phases should restore the published
feature shards rather than rebuild them.

The `features` stage (`STAGE = "features"`) is the Phase 6 family encoder run
of [PHASE6_FEATURES_PLAN.md](PHASE6_FEATURES_PLAN.md), a final stage under
budget pool C: the preflight runs at the `features` gate, the stage label is
`phase6_family_features`, and Cell 7 publishes under the `phase6_features`
stage on Drive. It calls `features build-families` with the tracked family
records, the all-train split manifest
`datasets/raw/augmentation/split_all_train_v1.json`, the pending list
`datasets/raw/augmentation/review/encoder_pending_v1.txt` and the Phase 4
identity `configs/phase6/phase4_feature_identity.json`; it makes no upstream
CAD fetch and needs no restored input. Before loading the encoder it compares
its repo_compatible identity with the Phase 4 values and stops, with
`identity_check.json` in the stage output, when a hash differs; otherwise it
encodes the 800 records once (6,432 passes) into one feature root per
representation mode and records the bundle manifest. Its progress steps are
family_identity_checked, resources_validated, the model-loading steps,
family_features_built and family_report_written. After publication,
`features check-families` verifies the restored output on CPU. The ordered
steps, including the gate rerun the stale tested profile needs first, are in
the plan's section "Before the encoder run".

Final stages reject candidate/unknown profiles. A tested profile requires Run A
and Run B manifest hashes, the reviewed commit and lock hash, matching runtime
values, and unchanged tested project code. A subsequent code fix requires review
and rerunning the affected full gate; it is not a Colab-side patch.

## Command Reference

Use `python -m rag_cad.cli --help` and the subcommand's `--help`. Commands are
`audit upstream`, `environment preflight`, `upstream fetch-cad`,
`upstream validate-cad`, `artefact publish`, `artefact restore`, `artefact verify`,
`smoke fake`, `smoke run-a`, `smoke run-b`, `data adapt-cad`, `data validate`, `data prescreen`, `data selfcheck`, `data split`,
`data check-leakage`, `data compare-budgets`, `features fake-build`,
`features build`, `features fake-build-families`, `features build-families`,
`features check-families`, `m0 fake-run`, `m0 run`, `conformance fake-released-test`,
`conformance released-test`, and `evaluation leak-excluded` (CPU post-hoc on a
restored m0 artefact; no gate). The default config paths are relative to the
repository working directory. All real smoke commands require explicit execution flags and
approved inputs. `features build` is a final
stage: it requires the tested profile, an approved compute budget, a resolved
`representation` in `configs/experiment.yaml` equal to the tested profile's
mode, the verified segmenter resources and the Jina bundle. It writes
content-addressed shards per pool and assembled condition sets
(`features.npz`, `rows.jsonl`, `manifest.json`) under one identity-claimed
output root, reusing a shard only after its identity and ordered record hashes
verify; `--resume` is required to reuse. `features fake-build` exercises the
same plumbing with the synthetic encoder on CPU and has no scientific meaning.
The `data` commands are CPU-only checks over project JSONL records and
need no `--execute` or profile, with one exception: `data validate --roundtrip`
requires the approved profile and the hash-verified segmenter resources so the
join-and-resegment check uses the frozen NLTK segmenter rather than a default.
`data split --all-train` puts every group in train with no validation or test
partition (the family feature build's manifest) and refuses records pinned to
test; it needs no split ratios. Otherwise `data split`, `data check-leakage`
and `data compare-budgets` refuse to run
while `split_ratios`, `near_duplicate_threshold` or `benign_length_tolerance`
are null in `configs/experiment.yaml`, and a failed leakage or budget check
still writes its report before exiting with status 2.

## Shared Budget And Storage

From 4 October 2026 the budget is four pools (D-20261004-17), each a hard cap on
connected time and compute units, whichever is reached first, carried forward
in the notebook inputs of its stages: pool A, bounded gate and conformance
runs, 6 hours and 12 units; pool B, Phase 4 final stages, 4 hours and 8 units;
pool C, Phases 5 and 6, 6 hours and 12 units; pool D, Phases 7 and 8, 8 hours
and 16 units. An exhausted pool needs a new decision entry, never a quiet
top-up. Runs before 4 October used 7,200 seconds and 1.84 units under the
original Phase 1B cap of **20 compute units or 10,800 connected seconds across
Run A plus Run B** (D-20260921-09); that usage is history and is not charged to
any pool. The runner takes the pool name and its two caps as inputs
(`BUDGET_POOL`, `POOL_CONNECTED_SECONDS_CAP`, `POOL_COMPUTE_UNITS_CAP`), checks
them against the approved profile's `compute_budget` block right after
checkout, and cuts every run off at the pool's remainder; the carry-forward
values are the pool's own cumulative usage. Select the lowest displayed-rate available NVIDIA GPU satisfying the
gate, preferring T4 when cheapest. Pro does not guarantee a GPU type. No premium
allocation or retry is implied by the subscription.

Use this operator cadence; ordinary notebook cells do not require repeated manual
budget checks:

1. Prepare and verify the entire input cell before connecting Colab. Leave live
   budget values ready to fill from the starting snapshot; do not invent them.
2. Connect a fresh runtime only when ready to execute the authorised run.
3. Take one starting snapshot immediately before execution: cumulative connected
   time from earlier Phase 1B sessions, cumulative compute units consumed, and
   the current displayed units/hour. Include any time/units already consumed in
   the fresh runtime before execution, so connected time is not omitted.
4. Insert those values and run the input and checkout cells back-to-back.
5. Once the checkout cell sets `STARTED = time.monotonic()`, rely on the
   notebook's automatic remaining-budget calculation. It continues to account
   for elapsed connected time between cells and rejects exhausted/invalid
   budgets. Do not reset `STARTED` or repeatedly replace the starting cumulative
   values with totals that already include that elapsed time.
6. Take another manual reading only after success, immediately after a failure,
   before fresh-runtime Run B, if Colab's displayed rate changes, or if either
   cap is genuinely close. Reconcile actual usage at those events; a changed
   rate must not be ignored or silently treated as the old rate. Stop before
   further work if the remaining allowance cannot be established conservatively.
7. Disconnect and delete the runtime immediately after completion or failure,
   or on reaching either cap. Command timeouts cannot stop Colab billing.
8. Never leave a paid GPU runtime connected while waiting for agent discussion.
9. Prefer Colab's actual balance difference where available; conservative rounding
   is sufficient when estimating usage. Do not interpret "between stages" as
   requiring minute-by-minute or cell-by-cell stopwatch updates.

The shared hard limits remain enforced by the existing budget calculation and
operator disconnect obligations; this cadence does not reset, extend, or weaken
either cap. It does not authorise execution, automatic retries, or Run B.

Runtime/Drive reservations are calculated from Ubuntu package evidence and
named-file sizes, without downloading Jina weights. Jina weights remain local
and are not redistributed. See the preparation evidence for byte counts and
safety margins. Drive capacity/access must still be confirmed manually.
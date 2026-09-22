# Colab Operator Runbook

## Current Gate

The Phase 1B live smoke gate passed: Run A and Run B from commit a822b9a0
completed in two fresh NVIDIA L4 runtimes and the resulting environment is
frozen as `configs/environments/colab_tested.yaml` with
`requirements/colab-core.lock.txt` under
[decision D-20260922-12](DECISIONS.md#d-20260922-12---freeze-the-tested-colab-environment-profile-from-run-a-and-run-b).
Final feature generation, training and evaluation must use that tested profile
and remain blocked until a bounded final-stage compute budget is approved
(`compute_budget_approved` is false), the primary representation is chosen
under D-20260921-05, and the data gates are complete. Any change to
`src/rag_cad` or `scripts/bootstrap_colab.py` after a822b9a0 invalidates the
tested profile until the gate is rerun. For the smoke gate, the standing
instruction applies: Daniel Song setting the two flags and running the runner
from a named commit is the authorisation for that commit. No code changes may
be made or pushed from Colab. The candidate profile remains for further
bounded smoke or conformance work.

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

Final stages reject candidate/unknown profiles. A tested profile requires Run A
and Run B manifest hashes, the reviewed commit and lock hash, matching runtime
values, and unchanged tested project code. A subsequent code fix requires review
and rerunning the affected full gate; it is not a Colab-side patch.

## Command Reference

Use `python -m rag_cad.cli --help` and the subcommand's `--help`. Commands are
`audit upstream`, `environment preflight`, `upstream fetch-cad`,
`upstream validate-cad`, `artefact publish`, `artefact restore`, `artefact verify`,
`smoke fake`, `smoke run-a`, `smoke run-b`, `data validate`, `data split`,
`data check-leakage`, and `data compare-budgets`. The default config paths are
relative to the repository working directory. All real smoke commands require
explicit execution flags and approved inputs; no final-training CLI is offered
yet. The `data` commands are CPU-only checks over project JSONL records and
need no `--execute` or profile, with one exception: `data validate --roundtrip`
requires the approved profile and the hash-verified segmenter resources so the
join-and-resegment check uses the frozen NLTK segmenter rather than a default.
`data split`, `data check-leakage` and `data compare-budgets` refuse to run
while `split_ratios`, `near_duplicate_threshold` or `benign_length_tolerance`
are null in `configs/experiment.yaml`, and a failed leakage or budget check
still writes its report before exiting with status 2.

## Shared Budget And Storage

The researcher approved at most **20 compute units or 10,800 connected seconds
across Run A plus Run B**, whichever occurs first, not per run. Select the
lowest displayed-rate available NVIDIA GPU satisfying the gate, preferring T4
when cheapest. Pro does not guarantee a GPU type. No premium allocation or retry
is implied by the subscription.

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
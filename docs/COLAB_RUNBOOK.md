# Colab Operator Runbook

## Current Gate

Phase 1A and its correction were merged through 45265a3b025aca50b1f13311efbd68aea9580d08. The bounded
CPU-only corrective pass is documented in [the corrective review](PHASE1A_CORRECTIVE_REVIEW.md).
The notebook is source, not permission to execute
it. The candidate template is intentionally unapproved and unresolved. Do not
download Jina/CAD binaries, mount Drive, or execute a real smoke until separately
authorised under D-20260921-02. No code changes may be made or pushed from Colab.

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
   than 8 GiB, and Python must be 3.12.x. Non-null expectations must match.
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
Scientific commands always run in new Python subprocesses, so the notebook
kernel never holds imported ML binaries across installation. A preflight failure
blocks mounting and execution. Work happens under the temporary workspace.

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
lookups therefore use the same verified local directory. Loading/inference uses
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
`smoke fake`, `smoke run-a`, and `smoke run-b`. The default config paths are
relative to the repository working directory. All real smoke commands require
explicit execution flags and approved inputs; no final-training CLI is offered
in Phase 1A.

## Shared Budget And Storage

The researcher approved at most **20 compute units or 10,800 connected seconds
across Run A plus Run B**, whichever occurs first, not per run. Select the
lowest displayed-rate available NVIDIA GPU satisfying the gate, preferring T4
when cheapest. Pro does not guarantee a GPU type. No premium allocation or retry
is implied by the subscription.

Enter actual cumulative time/units already consumed across both runs (including
time connected before the input cell) and Colab's displayed units/hour. The
launcher calculates conservative remaining command time and rejects exhausted
or invalid values. Recheck actual usage between stages and before Run B; update
the observations if rates change. Command timeouts cannot stop billing:
**the operator must disconnect and delete the runtime on completion, failure,
or reaching either cap**. No cloud execution is authorised by this preparation.

Runtime/Drive reservations are calculated from Ubuntu package evidence and
named-file sizes, without downloading Jina weights. Jina weights remain local
and are not redistributed. See the preparation evidence for byte counts and
safety margins. Drive capacity/access must still be confirmed manually.
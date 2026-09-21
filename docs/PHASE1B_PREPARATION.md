# Phase 1B CPU Preparation

## Scope

Base: `45265a3b025aca50b1f13311efbd68aea9580d08`.
Branch: `phase1b-preparation`; [PR #4](https://github.com/DanielS26/rag-cad-semantic-pairs/pull/4).
The original checkout and its notebook kernel metadata edit are preserved.
Preparation uses a fresh clean linked worktree at `../rag-cad-phase1b-prep`.
No GPU/Colab/Drive or secret access, model/data artefact download, remote-code
execution, research-data generation, decision entry, or merge occurred.

## Linux Candidate Lock

The lock was generated on Ubuntu x86-64 / Python 3.12.14 using pip-tools 7.4.1,
then installed into a fresh venv on a CPU-only GitHub runner. The full CUDA-capable
PyTorch package and its library dependencies were installed, not run on a GPU.
All tests use fake model/transport/hardware components. Installing a CUDA library
wheel does not constitute GPU or model execution.

- Source inputs: requirements/colab-core.in and requirements/dev.in.
- Lock: requirements/colab-core.candidate.lock.txt.
- SHA-256: `4d4624e4d23591ca6471818686bdcddbb59d80c53807e622423deb9a91939f43`.
- [Successful Ubuntu generation/install/test run](https://github.com/DanielS26/rag-cad-semantic-pairs/actions/runs/35552867275).
- Generation code commit: `98d64db763b3920f9686776c3a27b2a1c46cca82`.
- Raw CPU package/wheel/storage evidence is committed in
  [configs/environments/colab_candidate_cpu_evidence.json](../configs/environments/colab_candidate_cpu_evidence.json).
- The committed lock is byte-identical to the successful job artefact. LF Git
  attributes preserve the hash on Windows and Linux.
- CI now tests both the small dev environment on Windows/Ubuntu and installation
  of the complete committed Linux candidate lock on Ubuntu CPU for the PR head.

An earlier runner failed with insufficient disk while installing dependencies.
Only disposable runner Android/.NET/GHC tools and pip cache were removed to create
space; scientific dependencies were not weakened. No failure is hidden as a pass.

This is a tested **CPU installation of candidate dependencies**, not a tested
Colab environment and not a passed Phase 1B gate. The GPU, driver, CUDA/runtime,
real Jina/FAISS/PyTorch path, and Drive round trip remain live-smoke checks.

## Measured Storage Reservation

Package sizes are measured from the installed Ubuntu environment and selected
PyPI wheel metadata. Jina sizes come from the exact pinned repository metadata;
its weights were not downloaded. Values below are conservative reservations for
the bounded three-sentence smoke, not final feature generation.

| Quantity | Bytes |
|---|---:|
| Named Jina model/tokenizer files | 1,161,771,987 |
| Named remote-code reserve | 1,048,576 |
| Local model copies: download cache + verified bundle | 2 |
| Four named CAD files | 2,680,084 |
| NLTK compressed resource | 4,319,076 |
| NLTK extraction reserve | 268,435,456 |
| Compressed Linux dependency wheels | 4,263,907,370 |
| Installed candidate dependencies | 7,893,686,879 |
| Smoke working reserve | 2,147,483,648 |
| Runtime safety margin | 2,147,483,648 |
| Required runtime free space before installation | **24,696,061,952 (23 GiB)** |
| Required runtime free space after installation | **7,516,192,768 (7 GiB)** |
| Drive reservation for both smoke outputs, including partial copies | **134,217,728 (128 MiB)** |

Runtime pre-install reservation is the ceiling of installed dependencies + twice
compressed wheels + post-install reserve, with a 20 GiB floor. Post-install space
includes two model copies, segmenter/CAD inputs, smoke workspace, and margin.
The installer checks the first threshold before installing; preflight checks the
second. Drive reservation allows 32 MiB per run, doubled for partial publication.
Optional source-input archives require extra Drive space; Jina weights must never
be published or redistributed. Drive quota/sharing must be confirmed by the
operator because mounted filesystem free-space reports are not reliable quota
evidence. No Drive access was performed here.

## Discovery And Security

Approval and scientific/input pins are checked before hardware access. For
candidate smoke/conformance only, null Python patch/GPU/VRAM/CUDA/driver fields
are discovered rather than guessed. The runner records measurements, rejects
VRAM <=8 GiB or absent CUDA/driver, verifies Python 3.12.x and the complete locked
package set, then probes a tiny tensor operation. Mismatches produce failure
evidence and stop before models. Configured non-null values remain constraints.
Tested/final profiles permit no unknown values and must match exactly.
Run B must match Run A's measured environment; no automatic profile promotion.

The token is used only in the clone subprocess environment and cleared before
local checkout verification, bootstrap hashing, installation, or model work.
The runner executes only its verified local bootstrap and pinned local model/code
bundle. Drive mounts are restricted to restoration and publication with finally
unmounts. A local restore receipt is checked before Run B, allowing Drive to stay
unmounted during model loading/inference. Jina weight publication is refused.

## Approvals And Manual Actions

Operational clarification: this document preserves historical preparation
evidence. The current live operator cadence is governed by
[Shared Budget And Storage in the Colab runbook](COLAB_RUNBOOK.md#shared-budget-and-storage),
not the historical "between stages" wording below; the shared hard caps are unchanged.

The researcher approved later-smoke noncommercial academic use with attribution
and no Jina-weight redistribution; model revision
`ab036b023d30b4d1138c4c3bfa9f0c445ab455d6`; code revision
`bd55a5ec8e6c0fb1d6c26efb4b6a4a74ce8a88d3`; exact named downloads; and a shared
ceiling of **20 compute units or three connected hours for Run A plus Run B**.
These permissions are recorded in candidate configuration, not DECISIONS.md,
and do not authorise execution during this preparation pass.

Before a live run:

1. Review this PR and final CI, merge manually, and use its exact merged SHA and
   bootstrap file hash. Do not run from this task branch's moving name.
2. Explicitly approve the overall smoke candidate (including smoke-only
   repo_compatible/native float32/tolerance settings) and authorise execution.
   `approved` remains false and `proposal_only` true until that action; no fake
   researcher name or tested status is filled in.
3. Choose the lowest displayed-cost available NVIDIA GPU above 8 GiB, T4 if it
   is cheapest. Pro does not guarantee allocation. Let the runtime record and
   validate the actual GPU, Python, CUDA, driver, and dependency environment.
4. Confirm at least 128 MiB available Drive quota, sharing permissions and access
   to /content/drive/MyDrive/COMPSCI764_RAG_CAD/artefacts. Operator: Daniel Song.
   GH_READ_TOKEN is already prepared; never paste its value into the runner.
5. Enter actual cumulative connected time and compute units used (both runs,
   including time already connected) and the displayed units/hour. Commands use
   the smaller remaining allowance. Update actual usage/rate between stages.
6. Disconnect and delete the runtime on completion, failure or either cap.
   A process timeout cannot disconnect Colab billing. Record Run A usage before
   starting fresh Run B. Do not retry automatically on a different runtime.

GO for review of CPU preparation. Phase 1B execution remains gated by the exact
reviewed merged commit, overall smoke-candidate approval and separate execution
authorisation. No technical requirement to invent runtime values remains.
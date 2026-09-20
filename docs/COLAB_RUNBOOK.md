# Colab Operator Runbook

## Current Gate

Phase 1A is CPU-only. The notebook is committed source, not permission to execute
it. The candidate template is intentionally unapproved and unresolved. Do not
download Jina/CAD binaries, mount Drive, or execute a real smoke until separately
authorised under D-20260921-02. No code changes may be made or pushed from Colab.

## Before Phase 1B

1. Review the Phase 1A diff and passing CPU/CI checks. Merge using a merge commit
   to retain the pinned upstream ancestor. Record the exact resulting SHA.
2. Resolve and review the candidate Linux dependency lock, candidate GPU/Python/
   package fingerprint, encoder revision, temporary smoke representation,
   segmenter resource revision/hash, and numeric tolerances. The provisional
   `requirements/colab-core.in` is not an approved lock. Its generator is absent
   intentionally because Phase 1B uses a fake generator.
3. Produce and review `requirements/colab-core.candidate.lock.txt` in a separately
   authorised environment-preparation step. Do not relabel a Windows dev lock as
   a Colab lock. If local CPU implementation is missing, request bounded
   corrective authorisation before proceeding, as D-20260921-02 requires.
4. Populate and explicitly approve the candidate profile. Its `expected` mapping
   must match the runtime exactly; `lock_sha256` identifies the committed lock.
   `segmenter` is the canonical JSON SHA-256 of `segmenter_resource`, including
   its immutable NLTK-data revision and zip hash. No NLTK resource download occurs
   at import time. Expected versions include torch, transformers, numpy, nltk,
   scikit-learn, faiss-cpu, and huggingface-hub.
5. Confirm Drive path/operator/capacity. Set the reviewed storage config's
   `artefact_root` to the approved Drive artefact directory, not a working path.
6. Record the SHA-256 of `scripts/bootstrap_colab.py` from the reviewed commit.
   Supply the private repository read-only token in Colab Secrets as
   `GH_READ_TOKEN`. No token belongs in an input cell, Git URL, or saved output.

## Notebook Sequence

The output-cleared runner accepts an exact commit, bootstrap hash, approved
profile/lock paths, run ID, stage, and optional input manifests. It verifies the
downloaded bootstrap bytes before executing them. The helper uses temporary
askpass credentials, clones, detaches at the exact commit, checks upstream
ancestry, and removes the token from its child environment.

Installation, CPU tests, and preflight run before the explicit Drive mount cell.
Scientific commands always run in new Python subprocesses, so the notebook
kernel never holds imported ML binaries across installation. A preflight failure
blocks mounting and execution. Work happens under the temporary workspace.

For first acquisition, explicitly approve network use. Only four named CAD files
are downloaded at immutable revisions and verified before parsing/loading.
The pinned NLTK resource is also hash-checked and safely extracted. Alternatively,
restore an approved source bundle containing `upstream/` and `nltk_data/` into
the local `inputs/` directory. Existing mismatched/partial inputs are not silently
overwritten. Use a fresh run/destination after investigating failures.

Run A checks deterministic three-row features, released-checkpoint probabilities,
one synthetic-label MLP epoch/save/reload, tiny CPU FAISS serialization/retrieval,
and fake-generator checkpoint-swap invariants. The smoke MLP is not a primary
condition. Reports include provenance, tolerances, timings, output bytes, and
peak GPU memory. Three-row throughput is not a full-dataset runtime estimate.

Publish after the stage succeeds. The immutable artefact protocol writes the
success marker last and verifies payload/member hashes. Retain the published
Run A manifest and source bundles. Delete the runtime yourself; no local test
can demonstrate that action.

Start Run B in a fresh hosted runtime with the same reviewed commit/environment.
Restore the verified Run A bundle and compare its saved checkpoint predictions.
The command rejects the same runtime identity and mismatched provenance.
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
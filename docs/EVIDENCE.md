# Implementation Evidence

## Preserved Sources

CAD commit `26e38a67f0a9e1de4cb3a876e4b021900a5d1c27` was verified through the GitHub
API and integrated under D-20260921-08. Its detector, evaluation, benchmark,
original dependency input, original benchmark scripts, and licence are preserved.
The project adds its own package, tests, configs, scripts, and documentation.
The root README receives a project introduction and the root ignore file adds
project exclusions; those are explicit integration changes, not detector patches.

`python -m rag_cad.cli audit upstream` checks the pinned ancestor and preserved
source paths. Tests do not import upstream modules: those import AgentDojo and
download NLTK data at import time. Project equivalents are lazy and refer to the
preserved source under its MIT licence.

## Verification Boundaries

- [Release audit](project-plan/COMPSCI764_CAD_Release_Audit_2026-09-19.md) contains
  supplied historical hashes, schemas, counts, and static checkpoint findings.
  The Phase 1A manifest copies those expectations; no official binary was fetched
  or revalidated here.
- CPU tests use synthetic records, NumPy checkpoints, fake transports, fake
  encoder outputs, and fake generators/indexes. Fake Run A/B reports are labelled
  fake and never promote a profile.
- Hand-computed tests distinguish token-exclusion pooling from whole-input
  pooling. They do not establish real Jina/PyTorch numerical conformance.
- The real adapter uses pinned remote code and float32 and rejects inputs over
  8192 tokens instead of silently truncating. Real pooling tolerance remains an
  explicitly reviewed profile value. No primary representation is selected.
- Local filesystem round trips do not prove Drive mount, quota, copy, or restart
  behaviour. Run A and a fresh Colab Run B remain mandatory.
- The Windows development lock is separate from the untested Colab dependency
  input. No tested core lock or tested environment profile exists yet.

Executed commands/results belong in [PROGRESS.md](PROGRESS.md). Scientific and
material operational decisions require the approval workflow in
[DECISIONS.md](DECISIONS.md).

## Corrective Boundary

The merged scaffold's 54 passing CPU tests did not establish real-loader
readiness. The corrective pass separates weights/code revisions, provides
verified local-only model loading, strengthens actual-path/network guards, and
retains missing smoke evidence with checkpoint-backed synthetic swap tests.
See [the corrective review and candidate sheet](PHASE1A_CORRECTIVE_REVIEW.md).
No candidate setting is approved by adding it to configuration; real execution
and all Phase 1B acceptance results remain pending.
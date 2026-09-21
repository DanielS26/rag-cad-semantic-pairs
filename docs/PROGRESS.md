# Project Progress

Factual commands, results, and blockers belong here. Consequential decisions
require researcher approval and are recorded in [DECISIONS.md](DECISIONS.md).
Historical audit claims are distinguished from checks executed in this session.

## 2026-09-21 - Repository synchronisation and decision approvals

### Observed Starting State

- Read the start prompt and every available document listed in its Section 1 in
  the preceding planning turn. No implementation was performed.
- The preceding session created and successfully pushed the initial documentation
  commit 7c8754585f0f3b713aff4bf6c66d96b0baf9d229 to origin/main.
- `git --no-optional-locks status --short --branch --untracked-files=all` showed
  main tracking origin/main, seven deleted paths under project-plan, and seven
  untracked replacement paths under docs/project-plan.
- `git log --all -8 --format="%H %d %s"` showed only the initial documentation
  commit, with local main and origin/main at that SHA.
- `git ls-remote --heads origin` confirmed the live remote main was also
  7c8754585f0f3b713aff4bf6c66d96b0baf9d229 before the requested rewrite.
- `git switch -c sync-local-baseline-20260921` succeeded and retained the local
  documentation relocation.
- The repository contains no CAD source, upstream remote, package, dependency
  environment, tests, or CI. GitHub privacy and collaborator access have not been
  verified. Structural release audit results remain supplied historical evidence,
  not newly executed archive/model checks.

### Authorisations And Scope

- The researcher explicitly requested a local-authoritative published-history
  rewrite and synchronisation to main, superseding the earlier preservation
  proposal. See D-20260921-01.
- The researcher supplied the approved CPU-only Phase 1A and candidate/tested
  profile distinction. See D-20260921-02.
- The clarification question for "P3: okay" received the explicit answer
  "Yes, approve all four A-D". See D-20260921-03 through D-20260921-06.
- Created the confirmed decision log with the required template and approval
  policy. No earlier decision entries existed to replace.
- This is documentation and Git work only. Phase 1A implementation is not started;
  no installs, official artefact/Jina downloads, GPU use, Drive mount, or real
  smoke execution has occurred.

### Validation And Publication

- A read-only PowerShell validation passed: all six dated decision entries have
  the required fields; both new documents have valid local Markdown links and no
  trailing whitespace.
- `git ls-tree -r --name-only HEAD -- project-plan`, `git rev-parse HEAD:<path>`,
  and `git hash-object --path=<new-path> -- <new-path>` proved that all seven
  relocated planning files have identical Git blob hashes to their originals.
- No executable project test suite exists yet. These checks validate the
  documentation snapshot only, not the planned research implementation.
- The guarded baseline publication is pending at the time this entry is written.
  The resulting commit and remote verification will be reported in the session
  close-out rather than claiming a push succeeded in advance.

### Protected-Main Rejection And Revised Publication

- The repeated documentation checks passed. Editor diagnostics reported no
  errors, and `git diff --cached --check` passed. The staged summary contained
  seven R100 renames and the two new documentation logs.
- The authorised `git commit --amend` created local-only root commit
  ce3c0452c15dcc1100cf588b7bfd13bbe1a334c9. Its worktree was clean.
- An atomic push of that commit to main and sync-local-baseline-20260921, guarded
  by main's exact expected old SHA and the new branch's expected absence, failed.
  GitHub returned GH013: main prohibits force pushes and requires a pull request.
  Both remote ref updates were rejected; no published history was rewritten.
- The researcher chose "Keep protections; use a normal commit and PR". Recorded
  D-20260921-07 and marked D-20260921-01 superseded without removing its history.
- `git reset --soft 7c8754585f0f3b713aff4bf6c66d96b0baf9d229` on the unpushed sync
  branch preserved the index and all working files while restoring the published
  commit as the parent for a normal successor commit. No hard reset was used.
- Branch publication, PR creation, and merge are pending at the time of this
  entry; the session close-out will report their observed outcome. The preceding
  pending rewrite plan is historical and replaced by this protected PR workflow.

### Remaining Gates

- Separate Phase 1A implementation authorisation is still required.
- The local baseline does not satisfy the pinned-CAD ancestry/source-preservation
  prerequisite. Resolve upstream integration before claiming that gate passed.
- Representation selection, exact Jina revision, budgets/splits, shared-malicious
  tutor approval, generator/retriever/corpus settings, Drive access/operator, and
  live Colab Run A/Run B verification remain open.
- D0 and reference-checkpoint adoption and the schema/conformance policy are now
  approved, but approval is not evidence of implementation or successful runs.

## 2026-09-21 - Phase 1A Authorised

- The researcher authorised Phase 1A only, following approved decisions.
- The preceding documentation PR was manually merged as
  0379a810d85ffdb559330bbc4b5f6baad5ea6d13; local main was fast-forwarded and clean.
- GitHub CLI authentication and private-repository access were verified. Main
  requires PRs and prohibits force pushes. Collaborator access remains unverified.
- Created task branch phase1a-foundation from that reviewed main commit.
- GitHub API verified upstream CAD commit
  26e38a67f0a9e1de4cb3a876e4b021900a5d1c27. Recorded the separately approved
  history-preserving integration as D-20260921-08.
- Only Python 3.14, 3.13, and 3.9 were initially registered. Installed the
  plan's Python 3.12 interpreter (3.12.10) using the official user-scoped WinGet
  package; WinGet verified the installer hash. This is a local development
  interpreter, not an approved or tested Colab profile.
- Implementation, CPU tests, CI, and upstream import remain in progress. No CAD
  archive/checkpoint or Jina download, GPU execution, or Drive mount has occurred.

### Local CPU Scaffold Evidence

- Imported pinned CAD source through local merge commit
  75db76e4e1be25e1b7c1788f26731f251830ebab, with parents
  0379a810d85ffdb559330bbc4b5f6baad5ea6d13 and
  26e38a67f0a9e1de4cb3a876e4b021900a5d1c27. No history was rewritten. Upstream
  source-tree metadata was checked for prohibited model/data archive filenames
  before obtaining the source. The vendored optional benchmark source is
  preserved, not installed or executed.
- Created the isolated Python 3.12.10 `.venv`, development inputs and resolved
  lock, installable project-only package, configs, tests, CLI, and CI workflow.
  Root README/ignore additions are explicit; original detector, adversarial
  training, evaluation, third-party source, original requirements, benchmark
  scripts, and licence remain unchanged.
- `python -m pip install -r requirements/dev.lock.txt -e . --no-build-isolation`
  succeeded in the project venv. `python -m pip check` reported
  `No broken requirements found.` No PyTorch, Jina, Transformers, FAISS, or
  AgentDojo dependency was installed in this CPU environment.
- `python -m pytest tests -m "not gpu and not integration" -q` passed:
  **53 passed**. Tests cover candidate/tested stage restrictions, preflight
  refusal, preserved upstream source, synthetic release transport/hash/count
  validation, archive safety, extracted segmenter integrity, checkpoint
  weights-only loading through a fake loader, hand-computed representations,
  fake RAG checkpoint swaps, immutable artefact round trips, bootstrap secret
  cleanup, notebook structure, and fake Run A/Run B orchestration. Network
  connections are refused by the CPU test fixture.
- `python -m ruff check .` passed after excluding all preserved upstream Python
  from project linting. No upstream lint issues were repaired or hidden by
  changing upstream code. `git diff --check` passed.
- `python -m rag_cad.cli audit upstream` returned the pinned CAD commit and
  `source_unchanged: true`. The audit also verifies ancestry.
- The thin notebook passed nbformat validation and compilation of every code
  cell with empty outputs and null execution counts. No notebook cell was run.
  The notebook creation tool failed twice; a valid empty notebook was created
  and its cells were added using the notebook editor, then statically validated.
- Pylance initially selected global Python 3.14; changed the workspace editor
  interpreter to the tested project venv. Rechecking project diagnostics no
  longer reported the prior missing pytest/NumPy/project imports.
- Real adapter/backend functions remain execution-unverified. Fake smoke outputs
  do not count as Colab acceptance. The candidate config is unapproved with
  unresolved values; the provisional Colab dependency input is not a tested lock.
- No final datasets, full features, primary model training/evaluation, real
  generator, GPU operation, Drive mount, or official binary download was run.

### Review And Remaining Gates

- Local scaffold checks are complete; GitHub Actions on the published commit and
  researcher review/merge are still pending. Do not mark Phase 1A fully accepted
  until those results exist. Publish only after showing the diff/test evidence.
- The Phase 1A integration PR must use a merge commit, not squash/rebase, to retain
  approved CAD ancestry. Main protections remain enabled.
- Future Phase 1B requires approved candidate environment/model/segmenter/
  tolerance settings, reviewed Linux candidate lock, confirmed Drive/operator,
  exact reviewed project SHA, and separate execution authorisation. Missing
  implementation after review requires bounded CPU-only corrective authorisation.
- The handoff's "empty test suite" wording is incorrect: pytest returns a
  nonzero status when no tests are collected. Acceptance uses the substantive
  passing CPU suite instead. The original clone-first checklist is updated to
  the approved ancestry/source-preservation criterion in D-20260921-08.

### First Published CI Failure And Correction

- The researcher authorised committing/pushing the scaffold, opening a PR, and
  running CPU CI. Published scaffold commit ce9e51f on phase1a-foundation and
  opened [PR #2](https://github.com/DanielS26/rag-cad-semantic-pairs/pull/2).
- GitHub Actions run 35513130108 failed on Windows and Ubuntu during test
  collection: `ModuleNotFoundError: No module named 'rag_cad.data'`.
- Cause: inherited upstream `data/` ignore pattern also matched the project
  source directory. Local tests used its existing files, but Git had omitted the
  two adapter source files. Added a narrowly scoped exception for
  `src/rag_cad/data/*.py` without exposing raw datasets, and added a regression
  check for inherited ignore rules hiding project Python source.
- The correction is being validated before republishing. No CI success is
  claimed for ce9e51f; upstream source remains unchanged.

### Passing Fresh-Checkout And CI Evidence

- Correction commit 844afe6 tracks both adapter source files and the ignore-rule
  regression test. A fresh local clone of this committed branch passed all
  **54 CPU tests** using the existing tested dev interpreter; this checked the
  committed file set, not just the original working tree.
- Fresh Windows and Ubuntu GitHub runners installed the dev lock and editable
  package and passed pip check, all CPU tests, Ruff, the pinned-source audit,
  and the clean tracked-worktree check.
- Successful push run:
  https://github.com/DanielS26/rag-cad-semantic-pairs/actions/runs/35513252959
- Successful PR run:
  https://github.com/DanielS26/rag-cad-semantic-pairs/actions/runs/35513254852
- `gh pr checks 2 --json name,state,link` returned SUCCESS for both operating
  systems on both runs. Branch phase1a-foundation matched its remote and had a
  clean working tree before this factual documentation update.
- Project-file credential-pattern scan found no GitHub/Hugging Face token or
  private-key patterns before publication. This is a bounded pattern scan, not
  a claim to detect every possible secret.
- Phase 1A implementation and local/fresh-runner CPU checks are complete.
  [PR #2](https://github.com/DanielS26/rag-cad-semantic-pairs/pull/2) remains open
  for researcher review and a merge commit. Main was not changed by the agent.
  The merged SHA cannot be recorded until that review/merge occurs.
- No Phase 1B execution was authorised or performed. All live smoke, profile
  promotion, real-model conformance, and Drive gates remain unchecked.

## 2026-09-21 - Bounded CPU-Only Corrective Pass

- Phase 1A PR #2 was manually merged as
  7848aff703ed0af5fc4a851a86d18f32dff525e9. Its post-merge Windows/Ubuntu
  [CI run](https://github.com/DanielS26/rag-cad-semantic-pairs/actions/runs/35542730762)
  passed 54 CPU tests per platform, install, pip check, Ruff, and upstream audit.
  Earlier entries describing the PR as pending are historical, not current state.
- The researcher authorised one CPU-only corrective pass after a read-only audit
  found loader pinning, network/path guards, evidence retention, and scorer-swap
  coverage gaps. No Phase 1B execution is authorised.
- Fetched origin/main and verified the exact merged SHA, its presence in
  origin/main, and pinned CAD ancestry before creating phase1a-corrective directly
  from that SHA. The prior local PR branch was not used as the base.
- Researcher reports GH_READ_TOKEN is prepared in Colab Secrets. Its value was
  not requested, read, printed, or used in this pass. Future artefact root is
  confirmed as /content/drive/MyDrive/COMPSCI764_RAG_CAD/artefacts and operator as
  Daniel Song; these are recorded in storage config without accessing Drive.
- Corrective implementation and local CPU regression verification are in
  progress. Candidate revisions, dependencies, remote-code permission, attention,
  tolerances, licences, network scope, and budget remain proposals, not approvals.
- Public file-name/licence metadata was inspected only at proposed model revision
  ab036b023d30b4d1138c4c3bfa9f0c445ab455d6 and code revision
  bd55a5ec8e6c0fb1d6c26efb4b6a4a74ce8a88d3. No model weights, full snapshot, CAD
  release archive/checkpoint, or remote-code execution was obtained/performed.

### Corrective Results And Stop Gate

- Implemented separate weights/tokenizer and code revision fields, a named-file
  local model bundle with verified hashes and preserved original configs,
  explicit remote-code/network permission, offline loading/inference, and local
  cache placement. Tests mock all model loading and remote acquisition.
- Added actual source/resource/bundle/output/restore path containment, linked-path
  refusal, and direct-operation guards. Drive remains a storage-transfer location,
  never an active compute path. Approved compute budget is required before CLI
  hardware inspection.
- Preserved release validation and source manifests in published smoke evidence;
  added tensor/metadata checkpoint inspection, maximum token length, RAM/disk
  snapshots, UTC measurement times, and stage timings. Replaced callback-only
  scorer swaps with two tiny synthetic checkpoint-backed CADScorer instances.
- Added einops to the untested Colab input. Candidate pins and suggested settings
  are explicit but unapproved and proposal-only. No candidate Linux lock, tested
  profile, GPU fingerprint, or scientific decision was fabricated.
- Updated the thin notebook via the notebook editor and mechanically normalized
  its JSON metadata with nbformat. Static tests verify syntax, metadata identity
  and language, cleared outputs, command ordering, and permission guards. A CPU
  guard test exits before importing Colab or accessing any secret; no notebook
  runtime, remote code, model, or cloud stage was executed.
- Final local commands from the repository root using `.venv/Scripts/python.exe`:
  - `python -m pytest tests -m "not gpu and not integration" -q`: **77 passed**.
  - `python -m ruff check .`: **All checks passed**.
  - `python -m pip check`: **No broken requirements found**.
  - `python -m rag_cad.cli audit upstream`: pinned CAD commit and
    `source_unchanged: true`.
  - `git diff --check`: passed; corrective documentation links validated.
  - Editor diagnostics: no errors reported for changed project modules/tests.
- No packages were installed in this corrective pass. The full suite uses CPU
  fakes and synthetic fixtures with network connections denied. Real-runtime
  compatibility remains unverified; the earlier merged-main CI does not certify
  these new, uncommitted corrective changes.
- The [corrective review](PHASE1A_CORRECTIVE_REVIEW.md) contains the exact candidate
  approval sheet, remaining blockers, and proposed decision-log entries. No
  changes were made to docs/DECISIONS.md. The two candidate entries remain unwritten.
- Full tracked and new-file diff is provided as generated review material under
  `outputs/review/phase1a-corrective.patch`, excluded from Git. No commit, push,
  merge, or new CI run is authorised/performed in this pass.
- Recommendation: GO for code review and separately authorised publication/CI;
  merge only after review and same-commit CI. NO-GO for Phase 1B execution until
  candidate lock, observed runtime fingerprint, separate approvals, Drive access/
  capacity confirmation, and bounded execution authorisation are complete.

## 2026-09-21 - CPU-Only Phase 1B Preparation

- PR #3 merged at 45265a3b025aca50b1f13311efbd68aea9580d08. Fetched origin and
  verified that exact commit and CAD ancestry. Created phase1b-preparation from
  a clean linked worktree at that commit, under ../rag-cad-phase1b-prep.
- The original working notebook differs only in top-level kernel metadata:
  kernelspec replaced language_info. Cells are unchanged. The original notebook
  and branch were left untouched; no reset, stash, recreation, or overwrite.
- The researcher authorised Ubuntu CPU dependency resolution/install/testing and
  Windows/Ubuntu CI, a discovery-gate correction, secure ordering, storage
  estimation, and a PR, but not Phase 1B execution or merge.
- Later-smoke permissions were explicitly supplied for the two named Jina pins,
  noncommercial academic use with attribution and no weight redistribution,
  named downloads, and a combined cap of 20 compute units or 10,800 connected
  seconds, whichever is reached first. Recorded these limits in candidate config;
  overall profile approval and notebook PHASE1B_AUTHORISED remain false.
  No decision entries were written.
- Initial preparation passed 87 CPU tests and Ruff and was published as 9195339
  in draft [PR #4](https://github.com/DanielS26/rag-cad-semantic-pairs/pull/4).
- First Ubuntu lock job 35552532635 resolved dependencies but ran out of disk
  while installing PyTorch's CUDA library wheels on a CPU runner. No GPU was
  used and no model/data artefact was downloaded. The next job frees unused
  Android/.NET/GHC tools only on the disposable GitHub-hosted runner and purges
  the resolver cache. Candidate ML versions are unchanged.
- Commit 98d64db adds secure clone-only token handling, post-transfer Drive
  unmounts, local restored-input receipts, and shared-budget timeouts. 100 local
  CPU tests and Ruff passed before publication. These are fake tests, not live
  Colab evidence. Candidate-lock installation verification remains in progress.

### Candidate Linux Lock Verified

- Ubuntu CPU generation/install/test run
  https://github.com/DanielS26/rag-cad-semantic-pairs/actions/runs/35552867275
  succeeded at commit 98d64db763b3920f9686776c3a27b2a1c46cca82.
- Retrieved only the generated lock, package install report, and JSON evidence.
  The lock SHA-256 is
  4d4624e4d23591ca6471818686bdcddbb59d80c53807e622423deb9a91939f43.
  The committed lock exactly matches those bytes; .gitattributes enforces LF.
- Measured dependencies: 4,263,907,370 compressed wheel bytes and 7,893,686,879
  installed bytes. Calculated reservations: 23 GiB free before installation,
  7 GiB afterward, and 128 MiB Drive quota for both smoke outputs/partial copies.
  No model weights were downloaded to obtain these estimates.
- Candidate config now binds the lock hash and segmenter fingerprint. Only
  runtime-discovery fields remain unknown; full profile execution stays blocked
  pending overall approval. No tested profile was created or decision entry added.
- The original notebook kernel metadata edit remains untouched in the original
  checkout. The preparation runner is independently edited and output-cleared.
- See [Phase 1B preparation evidence](PHASE1B_PREPARATION.md) for storage arithmetic,
  approval boundaries, CI provenance, and operator actions. Final same-commit
  Windows/Ubuntu and full Linux candidate CPU CI are required before review close-out.

### Local Preparation Acceptance

- Final preparation suite: `python -m pytest tests -m "not gpu and not integration" -q`
  passed **105 tests** using the existing Windows Python 3.12.10 dev interpreter
  with this worktree's source path. This includes runtime-discovery success,
  <=8 GiB, absent CUDA/driver, failed allocation, package drift/missing pins,
  dependency check failure, disk shortage, unapproved/final profiles, restore
  receipt tampering, no weight publication, token cleanup, and combined budgets.
- `python -m ruff check .`: all checks passed.
- `python -m pip check`: no broken requirements found.
- `python -m rag_cad.cli audit upstream`: pinned CAD ancestor and
  source_unchanged true. No upstream detector or vendored benchmark edits.
- Notebook schema, all code-cell syntax, language/identity metadata and cleared
  outputs pass static tests. No cell, Colab runtime, GPU or remote code executed.
- `git diff --check` and documentation links pass. docs/DECISIONS.md is unchanged
  against the authorised base; no decision entries were written.
- Final review/merge and separate Phase 1B execution remain pending. Same-commit
  Windows/Ubuntu/full-candidate CI outcome will be reported on PR #4 and in the
  session close-out. Candidate CPU success does not freeze a tested environment.

## 2026-09-21 - Smoke Candidate Approval Flags

- The researcher approved the candidate at merged-main commit
  7830d588715cc8e607847ca93dec8ccdebabf2bc for bounded smoke testing only.
  Created phase1b-smoke-approval directly from that verified commit in a clean
  worktree; existing notebook edits in other worktrees were preserved.
- Changed only approved=true, approved_by=Daniel Song, and proposal_only=false
  in the candidate profile. Status remains candidate; tested evidence remains
  unset. Pins, dependencies, scientific settings, licence/download/security
  constraints, and the combined 20-unit/10,800-second budget are unchanged.
- Updated the directly affected profile test and added regression checks using
  the actual committed candidate: smoke configuration is accepted, but features,
  training and evaluation are still refused without tested status.
- Local CPU suite: 109 passed. Ruff, pip check and upstream audit passed.
  No runtime code or notebook was changed; no Phase 1B execution, GPU/Colab/Drive,
  secrets, model/data artefacts, or remote-code execution were accessed.
- Decision-log proposal is separate and unwritten. This branch requires PR
  review and passing same-commit CI; it must not be merged by the agent.
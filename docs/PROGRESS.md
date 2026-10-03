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
- The [corrective review](archive/PHASE1A_CORRECTIVE_REVIEW.md) contains the exact candidate
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

## 2026-09-21 - Sanitized Phase 1B Stage Diagnostics

- The researcher reported Cell 4 failed at execution commit
  c1fd5c5a0e34d0befbb92c74fde3badc83a8fa76 with the generic bootstrap subprocess
  error. The runtime is deleted; reported conservative cumulative usage is
  1,860 connected seconds and 0.42 compute units, carried forward across retries.
- Diagnostic branch fix/phase1b-stage-diagnostics starts from verified main
  4bff790c154d34561f3673d9423ca77ef22a324f. The failed execution's bootstrap hash
  remains historical: 6f92c1a4b603e525facfbf179c106df5158d0febac4876612cb7bffcab1a845e.
- The four install/test subprocesses now report only their fixed stage label
  and exit_code or timed_out. Spawn/other process failures use a fixed failed
  outcome. Raw commands, paths, URLs, environment, output and exception chains
  are not included in subprocess failure diagnostics.
- Audited the notebook and helper path: pre-bootstrap Git calls and later
  preflight/restore/fetch/smoke/publish subprocess calls needed equivalent
  sanitized boundaries. Notebook changes are diagnostic-only; successful CLI
  output is retained, failed output is suppressed. Arguments, command order,
  timeouts, cleanup, permission/hash/disk/budget guards and scientific behaviour
  are unchanged. Existing actionable guards and package CLI handling are retained.
- Local checks: 172 CPU/fake tests passed; Ruff, pip check, editor diagnostics,
  notebook schema/syntax/output-clearing checks and upstream audit passed.
  Tests inject fake secrets into failed output, commands and exceptions,
  including TimeoutExpired, and verify label/exit mapping and no disclosure.
  One static test's AST traversal order was corrected after its focused failure.
- This change diagnoses the failing stage, not its underlying cause. No
  dependency/profile/pin/lock changes, model/data downloads, secret access,
  Colab/GPU/Drive use, live notebook execution, or decision entries occurred.
- The updated thin runner must be used from the eventual reviewed merge SHA
  with its newly verified bootstrap hash and fresh execution authorisation.
  Existing historical hashes are not rewritten; no automatic retry or merge.
- Initial Windows CI run 35571731165 failed an existing timeout-bound assertion
  that used the live runner clock (171 other tests passed). Replaced that test's
  clock with deterministic readings and asserted the exact remaining timeout
  sequence. Production timeouts and budget code are unchanged; CI is rerun on
  the test-only correction. This is not a fix for the failed Colab execution.
## 2026-09-21 - PR #7 Merge Verification And Runner Input Preparation

- [PR #7](https://github.com/DanielS26/rag-cad-semantic-pairs/pull/7) was manually
  merged by Daniel Song at 2026-09-21T07:21:49Z as merge commit
  ffabf8369c18d162bee2cb8ea49e563f90501b6a, with parents
  4bff790c154d34561f3673d9423ca77ef22a324f (main) and
  3a16f462f1925d85863ff70a7aa4c57e33df32aa (reviewed head). The merge tree is
  byte-identical to the reviewed head; only the five reviewed files differ from
  the previous main. Pinned CAD ancestry is retained. No open PRs remain.
- Post-merge push [CI run 35572605522](https://github.com/DanielS26/rag-cad-semantic-pairs/actions/runs/35572605522)
  on the merge commit succeeded: cpu (ubuntu-latest), cpu (windows-latest) and
  candidate-linux all completed with conclusion success.
- Committed bytes at the merge commit: `scripts/bootstrap_colab.py` SHA-256
  6c61d1bc828b75b40961e2e1d461d336b04aea12c319318c6a2b4ce3ce054b61 (matches the
  reviewed head; the historical failed-execution hash 6f92c1a4... is unchanged);
  runner notebook blob 66b37130651e6046208a7941e4b2a5810552c702, file SHA-256
  396709ec68440d5cd96fd415eb47104ed8b68454a424e12d6abe42073cac0ab8, nbformat
  valid, all code cells compile, outputs and execution counts cleared. The
  committed candidate lock hash still equals the Ubuntu CPU evidence value
  4d4624e4d23591ca6471818686bdcddbb59d80c53807e622423deb9a91939f43.
- Local checks from the rag-cad-smoke-approval worktree at the merge commit,
  using the Windows Python 3.12.10 dev interpreter with this worktree's source
  path: 172 CPU/fake tests passed; Ruff passed; pip check passed; upstream audit
  returned the pinned CAD commit and source_unchanged true; git diff --check
  passed. Local main was fast-forwarded to the merge commit in that worktree.
- A disposable Cell 1 input block for Run A from the merge commit and new
  bootstrap hash was prepared for review outside the repository. It carries
  forward 1,860 connected seconds and 0.42 compute units and leaves the unit
  rate to be read at the starting snapshot. Authorisation flags remain false.
- No Colab, GPU, Drive, secret, model/data download, or notebook execution
  occurred. The old Run A authorisation, runner, run ID and bootstrap hash are
  not reused; execution from the merge commit requires fresh authorisation.
  The Cell 4 failure cause remains unknown and no dependency change was made.

## 2026-09-21 - Run A Attempt From ffabf836 And Environment Isolation Correction

- Daniel Song authorised Run A from ffabf8369c18d162bee2cb8ea49e563f90501b6a
  with bootstrap hash 6c61d1bc828b75b40961e2e1d461d336b04aea12c319318c6a2b4ce3ce054b61
  and executed the committed runner in a fresh Colab GPU runtime. Cells 2 and 3
  (inputs, clone, exact checkout and bootstrap hash check) passed. Cell 4 failed
  with the sanitized diagnostic `pip_check: exit_code=1`; the locked dependency
  install and editable project install stages therefore completed. The runtime
  was deleted after one read-only `pip check` diagnostic cell.
- Reported usage for the attempt: about 6 minutes and 0.2 compute units.
  Recorded conservatively as 360 connected seconds and 0.2 units, giving a
  carry-forward of 2,220 connected seconds and 0.62 units against the shared
  10,800-second/20-unit cap. The displayed unit rate was not re-read; it must be
  remeasured at the next starting snapshot.
- The `pip check` output listed eight broken requirements, all raised by
  Google-preinstalled Colab packages (ipython/jedi, google-colab, diffusers,
  datasets, gcsfs, gradio, cuda-python, torchvision) against the lock's requests,
  huggingface-hub, fsspec, cuda-bindings and torch versions. The ipython/jedi
  conflict exists before any project install. No conflict involved two
  project-locked packages; the candidate-linux CI job installs the same lock
  into an empty virtual environment and passes. Colab's image now ships torch
  2.11.0, so the locked install downgraded torch to the paper's 2.10.0.
- Daniel Song authorised one bounded CPU-only corrective pass and approved
  D-20260921-10. Branch fix/phase1b-venv-isolation starts from ffabf836. The
  bootstrap now creates a fresh isolated virtual environment outside the
  checkout (default `/content/rag-cad-venv`, rejected if inside the checkout or
  already present), installs the lock and project into it, runs pip check and
  the CPU tests with its interpreter, and returns that interpreter. A new
  sanitized stage label `virtual_environment_create` precedes the existing four.
  Cell 4 binds the returned interpreter and every later CLI command uses it;
  the notebook no longer references the kernel's sys.executable.
- Pins, lock, candidate profile, budget constants, scientific settings, command
  arguments, ordering, timeouts and secret handling are unchanged. This entry
  also carries the earlier PR #7 merge-verification entry above into the same
  branch instead of a separate documentation PR.
- Local checks on the corrective branch from the rag-cad-smoke-approval worktree
  with the Windows Python 3.12.10 dev interpreter and this worktree's source:
  179 CPU/fake tests passed (new: isolated-environment guard, venv stage in the
  deadline sequence and failure-label mapping, notebook interpreter binding);
  Ruff, pip check, upstream audit, notebook schema/syntax/cleared-output checks,
  documentation links and git diff --check passed.
- Not verified locally: that Colab's system Python can create a venv with a
  working pip, and that the isolated CUDA-enabled torch wheel sees the GPU.
  Both are live-gate checks; a failure will be reported by stage label. No
  Colab, GPU, Drive, secret, model/data download or notebook execution occurred
  in this pass. Execution from the resulting merge requires its new bootstrap
  hash and fresh authorisation.

## 2026-09-21 - Run A Attempt From 44dce5f3, Python 3.13 Re-lock And Venv Without Pip

- Daniel Song authorised and executed Run A from
  44dce5f300e9101913c07df1b45d3c1b1bd43836 with bootstrap hash
  dc1962b8d2dfbf3b2e0efb1983bbfb09a5b6cde91d0d6674448eba7086d405f6. Cells 2 and
  3 passed. Cell 4 failed with `virtual_environment_create: exit_code=1`. A
  read-only diagnostic cell showed `Python 3.13.15` at `/usr/local/bin/python`,
  `python -m venv` failing inside ensurepip, `No module named 'ensurepip'`, and
  no virtualenv or uv module. The runtime was deleted. Connected time and units
  for this attempt were not yet reported when this entry was written; the
  carry-forward remains 2,220 seconds and 0.62 units plus that attempt's usage.
- Two causes: Colab's Python build lacks ensurepip, and Colab's runtime is
  Python 3.13.15 while the candidate gate required 3.12.x, so preflight would
  also have failed after a full install. Daniel Song chose to re-target the
  candidate to Python 3.13 (D-20260921-11) over installing 3.12 inside Colab
  or relying on Colab's temporary fallback runtime.
- Branch fix/phase1b-python313-relock starts from 44dce5f3. The bootstrap now
  creates the isolated environment with `--without-pip` and installs the lock
  into it with the system pip's `--python` option; the lock pins pip 25.0.1
  and setuptools 80.9.0, so the environment then owns its pip. The candidate
  lock and candidate-linux CI jobs use Python 3.13.15 and the profile rule
  accepts 3.13.x only. The Windows/Ubuntu dev matrix remains Python 3.12.
- Commit ee822ff was pushed with seven failing tests because a pipe to `tail`
  masked pytest's exit code in the agent's command chain; the regex on the
  Python rule had not been updated. Its push CI and lock runs were cancelled
  and the correction committed as 9ef6123 (179 passed). Later chains enforce
  pipefail.
- First lock run 35595612985 on 9ef6123 resolved the lock on Python 3.13.15,
  passed pip check, 179 tests and Ruff, then failed in the evidence script:
  sentencepiece 0.2.0 has no Python 3.13 wheel on PyPI and was compiled from
  source, which the wheel-only storage accounting refuses. All 72 resolved pins
  were otherwise identical to the committed lock. PyPI metadata showed 0.2.1
  (2025-08-12) as the first release with a cp313 manylinux wheel; the input
  now requires sentencepiece==0.2.1 (commit b542456).
- Second lock run
  https://github.com/DanielS26/rag-cad-semantic-pairs/actions/runs/35596374112
  on b542456 succeeded. The committed lock is byte-identical to its artefact;
  SHA-256 1b270c043e4cbe273dd7c5e67b6f720bd9ec18a2b105ffcc83a7900d746f11e9.
  Evidence: Python 3.13.15, 72 named PyPI wheels, only sentencepiece changed
  (0.2.0 -> 0.2.1), compressed wheels 4,265,602,104 bytes, installed
  7,891,871,567 bytes, runtime/Drive reservations unchanged. The profile's
  expected lock hash and sentencepiece version were updated; approval flags,
  pins, model revisions, representation, tolerances and budget are unchanged.
  Push CI on b542456 passed Windows, Ubuntu and candidate-linux (3.13.15).
- Local checks on the final branch state from the rag-cad-smoke-approval
  worktree with the Windows Python 3.12.10 dev interpreter and this worktree's
  source: 179 CPU/fake tests passed; Ruff, pip check, upstream audit, notebook
  schema/syntax/cleared-output checks, documentation links and git diff --check
  passed. No Colab, GPU, Drive, secret, model/data download or notebook
  execution occurred in this pass. Execution from the resulting merge requires
  its bootstrap hash and fresh authorisation.

## 2026-09-22 - Run A Attempt From 75ed9c00 And Sanitized Smoke Progress Diagnostics

- Daniel Song authorised and executed Run A from
  75ed9c002688f315b997264fa6ac1740bd46723c with bootstrap hash
  59f196ff4f9aab3c5efecb3fefd31b6fd37519d98d66b1544b89cc9303312c85. Cells 2 to 5
  passed for the first time: the isolated environment was created without pip
  and populated from the lock; pip check, the CPU tests and preflight passed on
  an NVIDIA L4 (23,659,151,360 bytes), CUDA 12.8, driver 580.82.07, Python
  3.13.15, with all 72 locked packages verified and environment ID
  e9754028f076d94a9bca914bcb0db63bbfcf7fd6077677855f00ac6bb5ea355d.
- Cell 6 fetched and validated the pinned CAD release live for the first time:
  all four named files matched their expected SHA-256 values; original training
  parsed to 1,080 records, 24,665 rows, 1,625 malicious and 23,040 benign with
  zero count mismatches; original test to 389 records and 9,776 rows; the
  paraphrase bank to 3,376 records and 86,341 rows with the documented 1,278
  supplied-count mismatches. classifier_fullcad.pt loaded with weights_only on
  CPU, 557,698 finite non-constant parameters in the expected shapes.
- The smoke stage then failed with `smoke_run_a: exit_code=2`, the CLI's
  sanitized code for a refused operation. The exception class printed to
  stderr was suppressed by design, so the failing step is unknown. The runtime
  was deleted; connected time and units for this attempt and for the 44dce5f3
  attempt were not yet reported when this entry was written.
- Offline checks ruled out several candidates without GPU time: the pinned
  punkt_tab archive at nltk_data revision 550b6625 hashes to the expected
  e57f6418... value and the resource preparation/validation code passes on its
  real bytes; all five model and ten code files exist at the pinned Jina
  revisions; the released config's remote-code mapping matches the bundle
  transformation; transformers 4.57.1 assigns the local bundle directory as the
  model's name_or_path before the remote constructor loads its tokenizer; the
  remote code falls back to native attention and Torch rotary embeddings when
  flash-attention is absent and use_flash_attn is false; upstream CAD calls the
  model through forward().last_hidden_state exactly as the project does.
- Remaining candidates could not be separated offline: the model bundle
  download, model construction under transformers 4.57.1, non-determinism
  between the two encodes, or the reference-checkpoint scores. Branch
  fix/phase1b-smoke-diagnostics from 75ed9c00 therefore adds fixed-vocabulary
  progress steps written to `smoke_progress.json` in the workspace as each
  smoke stage completes (resource validation, segmenter check, bundle ready,
  tokenizer and model loaded, checkpoint loaded, output created, both encodes,
  determinism, reference scoring, training, reload, retrieval, RAG swap,
  report) and a `last_failure.json` record holding only the command labels and
  the exception class name. The smoke cell prints both files after the stage.
  Failed command output remains suppressed; no scientific setting, pin, lock,
  profile, argument or ordering changed.
- Local checks from the rag-cad-smoke-approval worktree with the Windows Python
  3.12.10 dev interpreter and this worktree's source: 183 CPU/fake tests
  passed (new: progress vocabulary/order and failure-position recording,
  failure record contents excluding exception text, progress reset per run,
  encoder progress steps, notebook diagnostics printing); Ruff, pip check,
  upstream audit, notebook schema/syntax/cleared-output checks and git diff
  --check passed. No Colab, GPU, Drive, secret, model/data download or notebook
  execution occurred in this pass. Execution from the resulting merge requires
  its bootstrap hash and fresh authorisation.

## 2026-09-22 - Run A Attempt From 39d1bab9 Located The Failure; Remote-Code Staging

- Standing instruction recorded: for the bounded smoke gate (Run A and Run B),
  Daniel Song setting PHASE1B_AUTHORISED and ALLOW_NETWORK to true and running
  the runner from a named commit is the execution authorisation for that
  commit. Explicit written authorisation remains required for final feature,
  training and RAG stages. Reported usage for the 44dce5f3 and 75ed9c00
  attempts together: 10 minutes and 0.3 units, recorded as 600 seconds and 0.3
  units; the carry-forward before the 39d1bab9 attempt was 2,820 seconds and
  0.92 units.
- Run A from 39d1bab91a5e4e613a723c3c77f4dad900a93532 (bootstrap hash
  59f196ff...) on an NVIDIA L4 passed install, preflight and live CAD release
  validation again. The new diagnostics reported progress
  `["resources_validated", "segmenter_checked", "model_bundle_ready",
  "tokenizer_loaded"]` and failure `{"command": "smoke", "action": "run-a",
  "exception_type": "FileNotFoundError"}`: the Jina bundle downloaded and
  verified, the project tokenizer loaded, and AutoModel.from_pretrained on the
  local bundle failed. Usage for this attempt is to be added when reported.
- Cause, confirmed from transformers 4.57.1 source
  (dynamic_module_utils.get_cached_module_file and get_class_in_module): for a
  local directory, transformers copies a remote-code file plus only its direct
  relative imports into its module cache, then hashes every recursive relative
  import there. The pinned code has two levels (modeling_lora imports
  modeling_xlm_roberta, which imports rotary, block, embedding, mha, mlp and
  xlm_padding), so the second level is absent and the hash step opens a missing
  file. Hub loading recurses and is unaffected, which is why upstream CAD's
  moving-revision load never met this.
- Branch fix/phase1b-remote-code-staging from 39d1bab9 adds
  stage_remote_code: after the bundle's revision and file-hash manifest are
  re-verified, the ten named code files are copied into transformers' own
  dynamic-module cache directory for the bundle (using the library's cache
  location, module namespace and name sanitisation) before loading. A new
  progress step `remote_code_staged` precedes `tokenizer_loaded`. No pin,
  lock, profile, notebook, bootstrap, argument or scientific setting changed.
- Local checks from the rag-cad-smoke-approval worktree with the Windows Python
  3.12.10 dev interpreter and this worktree's source: 184 CPU/fake tests passed
  (new: every verified code file staged into a fake dynamic-module cache with
  the library's hyphen sanitisation, tampered or wrong-revision bundles refused
  before staging, encoder progress order); Ruff, pip check, upstream audit and
  git diff --check passed. No Colab, GPU, Drive, secret, model/data download or
  notebook execution occurred in this pass.

## 2026-09-22 - Phase 1B Run A And Run B Passed; Tested Profile Frozen

- Usage for the 39d1bab9 attempt: 5 minutes and 0.15 units. Carry-forward before
  Run A: 3,120 seconds and 1.07 units.
- Run A from a822b9a032fc3d6c27261b25c62363fc3bc88142 (bootstrap hash
  59f196ff..., runner hash 49b3a2e5...) on an NVIDIA L4 (23,659,151,360 bytes),
  CUDA 12.8, driver 580.82.07, Python 3.13.15 completed all seventeen progress
  steps. Real Jina features: shape [3, 2048], float32, finite, identical across
  two encodes within atol 1e-6 / rtol 1e-5; feature time 0.43 s for three rows
  (6.9 rows/s including per-row context encodes); maximum token length 26;
  backend load 26.5 s; peak GPU memory 2,302,938,624 bytes. The released
  checkpoint produced finite non-constant probabilities (p_malicious about
  3e-11, 0.437 and 7e-08) and retained all three synthetic sentences at 0.5.
  One-epoch MLP trained, saved (SHA-256 e142ba93...), reloaded with matching
  predictions; FAISS round trip returned chunk 1 before and after; the
  fake-generator RAG pass kept retrieval, prompt-template and threshold hashes
  identical across no-defence and two synthetic checkpoints while only scores
  and retained text changed. Published and verified as run ID
  20260921T231238Z_a822b9a0_smoke_5bd0f99b; manifest SHA-256
  901cee9ae56cf91d89d1df50abb5ac29f481c20f893edc4bc8423dd608cdad2b as recorded
  by Run B. Usage: 8 minutes and 0.2 units.
- Run B from the same commit in a fresh L4 runtime (different runtime
  identity) restored the Run A artefact from Drive with all ten member hashes
  verified, re-downloaded the named CAD, NLTK and Jina files, reproduced the
  identical environment fingerprint and environment ID
  aed3f42347ddf55ec9c0b310865300b9b7dc90f99b151b71124ea0d1716296c1, reloaded the
  saved checkpoint and matched the saved predictions. Published and verified
  as run ID 20260921T232747Z_a822b9a0_smoke-run-b_5bd0f99b; manifest SHA-256
  05d322135aa734960d48d2a496f9a21f9b0b14d21d885836a96448433c9cb621 read from
  its `_SUCCESS` marker on Drive. Usage: 8 minutes and 0.15 units.
- Cumulative smoke usage: 4,080 connected seconds and 1.42 compute units of the
  10,800-second / 20-unit cap. Both runtimes were deleted after publication.
- Daniel Song approved D-20260922-12. Branch phase1b-tested-profile from
  a822b9a0 adds configs/environments/colab_tested.yaml with every measured
  value and both manifest hashes, requirements/colab-core.lock.txt as a
  byte-identical copy of the candidate lock, a regression test that the
  committed tested profile validates for smoke and final stages, keeps
  compute_budget_approved false, and rejects drifted or unknown runtime values.
  The candidate profile is unchanged. No src or bootstrap change, so the tested
  profile's code-identity check against a822b9a0 holds.
- Not yet established: the full feature-job estimate against the runtime and
  budget (the handoff checklist item stays open), the primary representation
  (D-20260921-05), the final-stage compute budget, and Drive sharing with the
  second researcher.

## 2026-09-22 - PR #12 Merged; Local Consolidation; Phase 2 Data Contracts And Leakage Controls

- PR #12 merged as 794e2b451eb0ebb56647835ea18e0aa259557de0 (parents a822b9a0
  and 681bf844, tree identical to the PR head, CAD ancestor 26e38a67 retained,
  CPU tests workflow green on the merge commit). Local main fast-forwarded.
- Local housekeeping approved by Daniel Song: the two linked worktrees
  (rag-cad-phase1b-prep, rag-cad-smoke-approval) were removed after confirming
  their only uncommitted differences were line endings and saved notebook
  outputs, so rag-cad-semantic-pairs is the single checkout, on main. Merged
  local branches were kept. The superseded downloaded runner under
  D:\COMPSCI764_RAG_CAD_Runs and the two prefilled Run A/Run B notebooks were
  moved to the Recycle Bin after confirming they held no secrets or outputs.
  The full CPU suite passed (185 tests) in the consolidated checkout on main.
- Phase 2 (handoff Section 10) implemented on branch phase2-data-contracts from
  794e2b45, CPU-only, with no Colab or budget use:
  - src/rag_cad/data/schema.py enforces the Section 7.1 record contract with
    frozen dataclasses and a strict validator: exact field sets, sequential
    sentence ids, integer 0/1 labels, malicious implies target, targets carry a
    semantic role, benign targets only in benign pair members, family_id
    exactly for paired members, condition_source and pair_member consistency,
    the licence registry, generator fields set together, and released CAD test
    or test_only records fixed to the test split.
    datasets/schemas/scorer_record.schema.json states the structure as JSON
    Schema.
  - src/rag_cad/data/jsonl.py: strict JSONL read and write (canonical lines, no
    overwrite, secret rejection, duplicate record_id refusal, file inventory
    hashes).
  - src/rag_cad/data/similarity.py: normalised word-shingle exact and Jaccard
    near-duplicate detection computed exactly over candidate pairs, with no
    probabilistic hashing.
  - src/rag_cad/data/validate.py: every family inside one group and holding a
    benign and a malicious member, differing-target diagnostics, the
    join-and-resegment round trip through split_units, exact duplicate records
    refused, cross-group duplicate diagnostics, and a dataset content digest.
  - src/rag_cad/data/split.py: group-level assignment (pinned and
    contract-fixed groups first, then seeded-hash order filled by ratio
    deficit; deterministic and independent of input order), a split manifest
    bound to the dataset content digest, apply_manifest, check_leakage (groups
    or families across splits, test families seen in training, exact or near
    duplicate records and target wording across splits are errors; benign
    context overlap is reported only) and training_records, the sanctioned
    training selector that refuses held-out records.
  - src/rag_cad/data/conditions.py: condition composition for M0-M3, document
    and sentence-level summaries, and compare_budgets (exact record, row and
    class equality across primary conditions, identical shared pools, complete
    augmentation units with equal benign sentence counts, optional
    character-ratio tolerance).
  - CLI: data validate, data split, data check-leakage and data
    compare-budgets. configs/experiment.yaml gains near_duplicate_threshold and
    benign_length_tolerance as unresolved null values; null split_ratios,
    threshold or tolerance refuse execution; a failed leakage or budget check
    writes its report and exits 2. data validate --roundtrip requires the
    approved profile and hash-verified segmenter resources.
  - tests/fixtures/phase2_families.jsonl: ten hand-written synthetic families
    (40 records) with equal per-unit sentence counts and character ratios of at
    most 1.18. New tests: test_data_schema.py, test_segmentation_roundtrip.py,
    test_family_leakage.py, test_equal_budget.py and test_data_cli.py (52
    tests). Full suite: 237 passed; ruff clean. Verified refusals: invalid
    labels or missing provenance, a deliberately leaked family, a count
    mismatch, a missing control variant, target wording crossing splits even
    as benign context, duplicate records across splits, and unresolved
    experiment values.
- Handoff checklist items ticked: five Phase 2 items plus the Section 15
  schema/validator, leakage-test and equal-budget items. "No test record is
  loaded by the training command" stays open until the Phase 6 trainer exists;
  that trainer must select rows only through training_records.
- Consequence for the tested profile: this branch changes src/rag_cad, so the
  tested profile's code-identity check against a822b9a0 no longer matches HEAD.
  Under D-20260922-12 the smoke gate must be rerun on the commit used for any
  final stage; no Colab run was made now.
- Not decided (candidates only, nothing written to DECISIONS.md): raw records
  carrying split null until assigned; the near-duplicate definition (word
  3-shingle Jaccard) and its threshold; benign context overlap reported rather
  than refused; split ratios and the D0 holdout policy (handoff Section 14 item
  4); the benign length tolerance.

## 2026-09-22 - PR #13 Merged; Phase 3 Representation Contract, Feature Builder And Generic Scorer (CPU Part)

- PR #13 merged as 89f0f987e07d78bb54afc8f8b39dc300000c7a74 (parents 794e2b45
  and 50d0a363, tree identical to the PR head, CAD ancestor retained, CPU tests
  workflow green on the merge commit). Local main fast-forwarded.
- Phase 3 (handoff Section 10) CPU-only part on branch
  phase3-representation-scorer from 89f0f987, with no Colab or budget use:
  - RepresentationConfig in src/rag_cad/cad/representation.py binds the mode,
    encoder and code revisions, segmenter fingerprint, dtype and attention
    into one representation_id; from_profile reads the tested profile; build()
    is the single feature implementation used by training-time builds and
    runtime scoring.
  - src/rag_cad/cad/fake_encoder.py holds the deterministic CPU stand-in
    encoder (moved out of the smoke fake backend) with a synthetic
    representation identity.
  - src/rag_cad/cad/feature_store.py writes and verifies feature sets:
    features.npz (X float32 [N, 2048], y int64 [N], loaded with allow_pickle
    false), rows.jsonl with the fifteen Section 7.2 metadata fields plus
    condition_source, and manifest.json with identity, counts, ordered record
    hashes, a row digest and file hashes. Reads verify every hash and the
    len(X) == len(y) == rows contract.
  - src/rag_cad/cad/feature_builder.py encodes validated, split-assigned
    records into content-addressed shards per pool (base, shared_malicious,
    random_benign, keyword_benign, semantic_benign, common_validation,
    common_test), reuses an existing shard only after verifying identical
    identity and ordered record hashes, refuses a root claimed by another
    identity, and assembles conditions by stable (record_id, sentence_id) row
    identity so M1-M3 share byte-identical D0 and malicious rows. Training
    pools are selected only through training_records.
  - CADScorer gains a fixed 0.5 threshold, representation_id,
    from_representation() and score_passage(), which returns a ScoredPassage
    (Section 7.5: sentences, probabilities, decisions, retained and removed ids
    and text, threshold, checkpoint and representation ids, segmentation and
    scoring latency). RAGPipeline evidence now logs retained and removed text
    and refuses a scorer whose threshold is not the contract value.
  - Run A now compares both representation modes on its three-sentence sample
    (shape, finiteness, determinism, runtime, released-checkpoint
    probabilities and decisions, identical isolated block, contextual
    difference) under a new progress step, modes_compared, and records the
    result as representation_modes in run_a.json. This stands in for a
    separate cad conformance command and notebook stage: the next gate rerun
    produces the D-20260921-05 evidence at no extra budget, and the report
    selects no mode.
  - CLI: features fake-build (CPU plumbing) and features build (a final stage:
    tested profile, approved budget, experiment representation resolved and
    equal to the tested profile's mode, verified segmenter resources and the
    Jina bundle). experiment.yaml representation stays null, so the real build
    refuses until D-20260921-05 is resolved.
  - Tests: test_feature_metadata_alignment.py, test_rag_filter.py,
    test_features_cli.py and additions to test_cad_conformance.py and
    test_smoke.py (14 new). Full suite: 251 passed; ruff clean.
- Handoff checklist items ticked: six Phase 3 items (both modes return 2048-d
  vectors, one implementation for training and runtime, tensor and metadata
  alignment, clear checkpoint-incompatibility errors, three-sentence passage
  scoring, no AgentDojo dependency) and the Section 15 feature-builder and
  generic-scorer items. Still open: "the selected mode is deterministic in
  eval mode" and the real-encoder conformance record with its environment ID,
  both waiting on the primary-mode decision and the next Colab gate; the
  trainer and registry belong to Phase 6.
- Not decided (candidates only): feature storage as features.npz rather than
  features.pt (no pickle; loads straight into torch tensors); the
  representation_id definition; the default shard size of 256 records; keeping
  the mode comparison inside Run A rather than a separate conformance command.

## 2026-09-22 - PR #14 Merged; Run A And Run B Passed From 0cc9ad77 With Representation-Mode Evidence

- PR #14 merged as 0cc9ad7754df6b3875758bbef8216c1d728126f1 (parents 89f0f987
  and 14743c4d, tree identical to the PR head, CAD ancestor retained, CPU tests
  workflow green on the merge commit). Local main fast-forwarded. The runner
  notebook (49b3a2e5...) and bootstrap (59f196ff...) are byte-identical to the
  a822b9a0 versions.
- Purpose of the rerun: the tested profile's code identity no longer matched
  HEAD after Phases 2 and 3, Run A's own script had changed, and D-20260921-05
  needed real-encoder evidence for both modes. The standing smoke instruction
  applied. Disposable prefilled notebooks were generated outside Git for
  commit 0cc9ad77 with the candidate profile and candidate lock.
- Run A (run ID 20260922T143040Z_0cc9ad77_smoke_5bd0f99b) on a fresh NVIDIA L4
  (23,659,151,360 bytes), CUDA 12.8, driver 580.82.07, Python 3.13.15, lock
  1b270c04...: preflight passed with the same fingerprint as on 21 September
  and environment ID
  25f3118172ded3c2918236aa7e93029d8cbe1716441aa6c56da360e475b22991 (differs
  from aed3f423... only through the commit); all eighteen progress steps
  completed, including the new modes_compared; features [3, 2048] and
  deterministic; backend load 26.1 s; feature time 0.43 s; maximum token
  length 26; peak GPU memory 2,302,938,624 bytes; released-checkpoint
  probabilities 3.0e-11, 0.437 and 7.0e-08, identical to the a822b9a0 run;
  one-epoch MLP saved (SHA-256 20698594...), reloaded and matched; FAISS round
  trip and checkpoint-swap invariants held, with retained and removed text now
  in the evidence. Published and verified; manifest SHA-256
  8d68633803262f0f0490d96bbaf53cb7125ad99e3c638cc2d617b3ab0f247140 as recorded
  by Run B. Usage: 9 minutes and 0.13 units.
- Representation modes (Run A key representation_modes): both modes finite and
  deterministic at [3, 2048], 0.265 s and 0.264 s; isolated blocks identical;
  largest contextual difference 0.111; the released checkpoint gives 0.437
  (repo_compatible) against 0.569 (paper_exact) for the synthetic target
  sentence, so removal decisions differ at 0.5 while both modes agree on the
  two benign sentences. No mode selected. Measurements and decision options are
  in [REPRESENTATION_MODES.md](REPRESENTATION_MODES.md).
- Run B (run ID 20260922T143040Z_0cc9ad77_smoke-run-b_5bd0f99b) in a fresh L4
  runtime (different runtime identity) restored the Run A artefact from Drive
  with hashes verified, re-downloaded the named CAD, NLTK and Jina files,
  reproduced the identical fingerprint and environment ID, reloaded the saved
  checkpoint and matched the saved predictions; published and verified. Its
  manifest SHA-256 has not been read from the Drive _SUCCESS marker; it is
  needed only if a profile is frozen from this pass. Usage: 9 minutes and
  0.10 units.
- Cumulative smoke usage: 5,160 connected seconds and 1.65 compute units of the
  10,800-second / 20-unit cap. Both runtimes were deleted after publication.
- No new tested profile was frozen from this pass: it would be invalidated by
  the next code change, and if the other mode is chosen D-20260922-12 requires
  the gate in that mode anyway. The a822b9a0 tested profile stays committed;
  final stages remain blocked by code identity, the null representation and
  compute_budget_approved false.

## 2026-09-23 - Released Test-Set Evaluation Stage For The Representation Decision

- Oracle search: the paper (arXiv 2608.05430v1), the CAD-models model card and
  the CAD-data dataset card report no sentence-level detector metric for the
  base classifier (the paper reports agent-level clean utility, utility under
  attack and attack success rate on AgentDojo and AgentDyn with seed
  statistics; the cards give descriptions and counts). The pinned upstream
  evaluator computes AUPRC, ROC-AUC and TPR/FPR at 0.5 on boundary-masked rows
  without published expected values. "Reproduce the paper's number" is not
  available; recorded in REPRESENTATION_MODES.md with the revised test.
- Upstream fidelity check: detector/defense.py joins the query and sentences
  with single spaces, pools the mean over tokens that are kept and attended
  with a plain-mean fallback, and truncates at 8,192 tokens. The project's
  repo_compatible mode matches, except that over-length inputs are refused and
  listed rather than truncated.
- Branch phase4a-released-test-evaluation (on top of the PR #15 docs branch),
  CPU-only, no Colab use:
  - src/rag_cad/evaluation/detector_metrics.py: NumPy average precision
    (step-wise over distinct thresholds), rank-based ROC-AUC with tie
    averaging, confusion counts and rates at a threshold under the upstream
    ">=" rule and the deployed ">" rule, the upstream boundary mask, and a
    summarise helper; verified against reference values and hand-computed
    masks.
  - src/rag_cad/operations/released_test.py: loads testing_data_original in
    the upstream sorted-path order with the domain taken from the first path
    component, scores each record under both modes with the reference
    checkpoint, and writes predictions.jsonl and released_test_evaluation.json
    (all-row, masked and per-domain metrics per mode, decision agreement,
    higher masked AUPRC, timings, token lengths, skipped over-length records,
    resource snapshots, peak GPU memory). It selects no mode. Four new progress
    steps.
  - CLI: conformance fake-released-test (CPU) and conformance released-test,
    gated at the conformance stage (candidate profile allowed, remote-code
    approval and tolerances required, no ML import before the gate), with
    --records and --domains.
  - Runner notebook: STAGE "released-test", input RELEASED_TEST_RECORDS, stage
    label conformance_released_test added to the bootstrap STAGES (bootstrap
    SHA-256 now a9560056cba18e6d83da0326dd584afff81028333769ddb73222e0efb8e57e6c),
    publish stage "conformance". The contract test now requires a literal
    stage-label map keyed by STAGE.
  - Tests: test_detector_metrics.py, test_released_test.py and
    test_conformance_cli.py (15 new). Full suite: 266 passed; ruff clean.
- Not run: no Colab execution. A ten-record pilot needs explicit
  authorisation; the full 389-record run needs a budget approved from the
  pilot's measured cost.
- Convention adopted at Daniel Song's request: every pull request title starts
  with the handoff phase code the work belongs to, in exactly the form
  "Phase N: <What the pull request does>", and carries the matching lower-case
  GitHub label (phase-0 to phase-4a created on 23 September; PRs #1 to #16
  retitled and labelled). Fix-up and documentation-only pull requests take the
  phase they serve. Recorded in handoff Section 1 (item 13) and in the
  repository's CLAUDE.md. Phase 4A (released-test conformance and the
  representation decision) is now described in handoff Section 10 so the code
  matches the label; PR #16 belongs to it.
- Documentation tidy-up approved by Daniel Song: docs/README.md added as the
  document map (each file, its job, living or frozen); the data card retitled
  "Data Card"; PHASE1A_CORRECTIVE_REVIEW.md moved to docs/archive with history
  preserved; EVIDENCE.md removed, its standing upstream-boundary paragraph
  folded into the root README's new "Upstream Code, Project Code And Records"
  section and its Phase 1A verification snapshot dropped because every item is
  recorded here by date; the literature guide left in place; the handoff's
  Section 6 tree and CLAUDE.md updated.

## 2026-09-23 - PR #17 Merged; Released-Test Pilot Passed From f4181bc8; Shared Encoder Passes

- PR #17 merged as f4181bc807d1161633cef671db8c69dfcdfa73ab (parents d3bfc779
  and 406651f8, tree identical to the PR head, CAD ancestor retained). Local
  main fast-forwarded. The runner notebook (8bbd19dc...) and the bootstrap
  (a9560056...) are unchanged since PR #16.
- Ten-record pilot of the released-test stage, authorised by Daniel Song on
  23 September. A disposable prefilled notebook was generated outside Git for
  commit f4181bc8 (STAGE released-test, RELEASED_TEST_RECORDS 10, candidate
  profile and lock, carry-forward 5,160 s and 1.65 units).
- Pilot run (run ID 20260923T060056Z_f4181bc8_released-test-pilot_5bd0f99b)
  on a fresh NVIDIA L4, CUDA 12.8, driver 580.82.07, Python 3.13.15, lock
  1b270c04..., environment ID 656a7c4a... (the smoke fingerprint at this
  commit): release validated with all four file hashes matched and the
  checkpoint safely loaded; eleven progress steps completed through
  released_test_report_written; no over-length records; 10 records, 180 rows,
  99 malicious and 81 benign, 80 malicious rows masked out by the upstream
  boundary rule; maximum token length 338; backend load 27.1 s; encoding
  14.57 s (paper_exact) and 14.67 s (repo_compatible), 6.16 rows/s over both
  modes; stage total 29.3 s; peak GPU memory 2,328,180,736 bytes. Published
  under artefacts/conformance/ with the run ID and verified; predictions
  SHA-256 4f205ec6.... Usage: 9 minutes and 0.07 units. Cumulative usage
  against the shared cap: 5,700 connected seconds and 1.72 compute units of
  10,800 s / 20 units. The runtime was deleted after publication.
- Pilot metrics (released checkpoint, threshold 0.5, identical under the ">="
  and ">" rules): all 180 rows, AUPRC 0.8910 (paper_exact) against 0.8908
  (repo_compatible), ROC-AUC 0.8666 against 0.8662, TPR 0.394 and FPR 0.0 in
  both modes; upstream-masked 100 rows (19 positives), AUPRC 1.0, ROC-AUC 1.0,
  TPR 1.0 and FPR 0.0 in both modes; decision agreement between modes 1.0;
  neither mode has the higher masked AUPRC. No mode selected. On this subset
  the fit test does not separate the modes; recorded in
  [REPRESENTATION_MODES.md](REPRESENTATION_MODES.md).
- Defect found by the pilot: every row was attributed to the domain
  "testing_data_original" because the archive's root folder was taken as the
  first path component. The pinned upstream evaluator (detector/
  train_and_eval.py, build_eval_mask) defines the domain as the first
  directory under the extracted test folder (banking, slack, travel). Fixed on
  branch phase4a-pilot-record: record_domain strips the archive folder and
  mirrors the upstream rule; the test fixture now carries the real layout.
- Cost reduction before the full run: the two modes share every encoder pass
  (the full passage, each sentence alone, the passage without each sentence)
  and differ only in which tokens of the first contextual term are pooled.
  The stage now builds both modes from one set of passes (build_mode_features;
  the single-mode build_features delegates to it with unchanged output), so
  encoder work per record falls from 2 + 4n to 1 + 2n forward passes. The
  report records encoder_passes and one encode_both_modes timing. Tests:
  shared-pass count and equality with the per-mode builder, suite derivation,
  report fields. Full suite: 268 passed; ruff clean.
- Full-run estimate from the pilot: 740 encoder passes took 29.2 s (39.5 ms
  per pass). The full set needs 389 + 2 x 9,776 = 19,941 passes, about 13
  minutes at pilot passage lengths and up to about 26 minutes if longer
  passages double the per-pass time, plus about 9 minutes of clone, install,
  downloads and model load: 22 to 35 minutes connected and 0.2 to 1.1 units.
  The remaining shared cap is 5,100 s (85 minutes) and 18.28 units. The full
  run awaits its own authorisation and budget.

## 2026-09-24 - PR #18 Merged; Full Released-Test Run Passed From d0b92eeb; The Fit Test Does Not Separate The Modes

- PR #18 merged as d0b92eebfe7e3084dfa15a2fa57265bfcf729f09 (parents f4181bc8
  and d6cffbf8, tree identical to the PR head, CAD ancestor retained, CPU
  tests workflow green on the merge commit). Local main fast-forwarded. The
  runner notebook (8bbd19dc...) and the bootstrap (a9560056...) are unchanged.
- Full released-test run authorised by Daniel Song by running the prefilled
  notebook generated outside Git for commit d0b92eeb (STAGE released-test,
  RELEASED_TEST_RECORDS 0, candidate profile and lock, carry-forward 5,700 s
  and 1.72 units, so the notebook cuts off at the remaining 5,100 s of the
  shared cap).
- First attempt (24 September local time) failed in Cell 4 at
  environment_preflight with exit code 2, a refused CLI command: nothing was
  loaded or published. The preflight code is unchanged since the pilot, so
  the runtime differed. The cause was not captured, because the retry was
  made before the runtime type or the failure line in preflight.json was
  reported; a missing or unallocated GPU is the likely cause. The retry with
  the same notebook and run ID on an L4 runtime passed. The run ID had not
  been used on Drive because the first attempt published nothing.
- Full run (run ID 20260923T080927Z_d0b92eeb_released-test-full_5bd0f99b,
  stage window 13:42 to 13:56 UTC on 23 September) on a fresh NVIDIA L4,
  CUDA 12.8, driver 580.82.07, Python 3.13.15, lock 1b270c04..., environment
  ID 0b72038d... (differs from the pilot's 656a7c4a... only through the
  commit): release validated with all four file hashes matched and the
  checkpoint safely loaded; eleven progress steps completed; 389 records and
  9,776 rows scored, none over length; maximum token length 529; 3,729
  malicious rows, 3,112 of them masked out by the upstream boundary rule,
  leaving 6,664 masked rows with 617 positives; domains banking 5,555 rows,
  slack 1,230, travel 2,991; 19,941 encoder passes, exactly the estimate;
  encoding 823.6 s for both modes (41.3 ms per pass, 11.9 rows/s); stage
  total 824.4 s; backend load 25.0 s; peak GPU memory 2,354,481,152 bytes.
  Published under artefacts/conformance/ with the run ID and verified;
  predictions SHA-256 3a727361.... Usage reported by Daniel Song for the
  notebook's two attempts together: about 25 minutes connected and 0.12
  units. Cumulative usage against the shared cap, counting released-test
  runs with the smoke attempts: 7,200 connected seconds and 1.84 compute
  units of 10,800 s / 20 units, leaving 3,600 s and 18.16 units.
- Metrics (released checkpoint, threshold 0.5, identical under the ">=" and
  ">" rules), paper_exact against repo_compatible: upstream-masked AUPRC
  0.98161 against 0.98131, ROC-AUC 0.99907 against 0.99906, TP 606 against
  605 of 617, FP 9 in both (FPR 0.00149); all rows AUPRC 0.8303 against
  0.8291, ROC-AUC 0.8853 against 0.8842, TP 1,384 against 1,383 of 3,729,
  FP 9 in both; per domain (masked) banking AUPRC 0.9667 against 0.9664 with
  272 of 272 detected and 9 false positives in both, slack AUPRC 1.0 in both
  with 102 against 100 of 105 detected, travel AUPRC 1.0 in both with 232
  against 233 of 240 detected. Decision agreement between the modes 0.99969:
  three rows of 9,776 differ. The report's higher_masked_average_precision
  names paper_exact, by 0.0003, one row's worth. No mode selected.
- Reading: the released checkpoint fits both recipes equally. The recipes
  differ only by the sentence's own share of the passage mean in the first
  contextual term, which is a few per cent for passages averaging 25
  sentences; the three-sentence smoke sample showed the largest differences
  for the same reason. The fit test is therefore in its "small gap" case and
  the decision falls to provenance and any author reply, as anticipated. The
  full-run numbers and the explanation are recorded in
  [REPRESENTATION_MODES.md](REPRESENTATION_MODES.md). A decision entry is
  proposed for the tutor meeting; nothing is written to DECISIONS.md and
  configs/experiment.yaml keeps representation null until it is approved.
- Handoff Phase 4A checklist: the full-run item is ticked; the decision item
  remains open.

## 2026-10-04 - Representation Decision Recorded; Implementation Choices Batched; Budget Proposal

- Resuming after a break since 24 September: PR #19 still open with CI green
  and mergeable; main unchanged at d0b92eeb; no other work recorded in the
  interval.
- Daniel Song approved the representation proposal ("yes go with that"):
  recorded as D-20261004-13, repo_compatible primary and paper_exact
  secondary. configs/experiment.yaml now sets representation:
  repo_compatible, which the candidate profile already expected. The smoke
  gate rerun that D-20260922-12 requires is scheduled for the commit from
  which the first final-stage run is launched, not earlier, because the
  Phase 4 code that follows would invalidate a profile frozen now.
- Daniel Song asked for one batched entry for the implementation choices of
  Phases 2 to 4A that had been listed as decision-log candidates: recorded
  as D-20261004-14 (thirteen items).
- Handoff: Phase 0 checklist item "Decide repo_compatible versus paper_exact"
  ticked; Section 14 question 1 marked resolved; the Phase 4A checklist item
  split so the recorded decision is ticked and the gate rerun stays open.
  REPRESENTATION_MODES.md and the representation module docstring state the
  decision.
- Open: the unresolved experiment values (split ratios, D0 holdout policy,
  near-duplicate threshold, benign length tolerance, augmentation budget,
  shared-malicious approval) stay null pending the tutor; a compute budget
  for the final stages was proposed to Daniel Song and awaits approval
  before it is recorded and enforced.
- Branch phase4a-representation-decision, stacked on PR #19. Full suite: 268
  passed; ruff clean.
- Later the same day Daniel Song approved the suggested defaults for the
  unresolved experiment values: recorded as D-20261004-15. configs/
  experiment.yaml now sets split_ratios 0.7/0.15/0.15 by family,
  d0_holdout_policy none, near_duplicate_threshold 0.8,
  benign_length_tolerance 0.25 and shared_malicious_additions true;
  augmentation_budget_sentence_rows stays null until the family pilot
  measures rows per family, and shared_malicious_tutor_approval stays null
  until the tutor's confirmation is recorded. Handoff Phase 0 checklist and
  Section 14 questions 3, 4 and 9 annotated; data card updated. Branch
  phase0-experiment-values, stacked on PR #20. Full suite: 268 passed; ruff
  clean.
- Still open: the final-stage compute budget (proposal of 2026-10-04 awaiting
  approval) and the authors' reply or its absence.

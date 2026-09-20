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
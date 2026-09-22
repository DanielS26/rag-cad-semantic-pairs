# Repository conventions for coding agents

Read `docs/project-plan/COMPSCI764_Project_Implementation_Handoff.md` Section 1 before
changing anything; it is the authoritative brief. The conventions below repeat the ones that
apply to every change.

- **Pull request titles** start with the phase the work belongs to, in exactly the form
  `Phase N: <What the pull request does>`: capital P, space, the phase code from handoff
  Section 10 (0, 1A, 1B, 2, 3, 4A, ...), colon, space, then a capitalised description.
  Example: `Phase 1B: Freeze the tested Colab profile from Run A and Run B`.
- **Pull request labels**: every pull request carries the matching lower-case label
  (`phase-0`, `phase-1a`, `phase-1b`, `phase-2`, `phase-3`, `phase-4a`, ...). When a new
  phase starts, create its label first:
  `gh label create phase-N --repo DanielS26/rag-cad-semantic-pairs --description "Phase N: <one line>"`,
  then attach it: `gh pr edit <number> --repo DanielS26/rag-cad-semantic-pairs --add-label phase-N`.
  Fix-up, documentation-only and corrective pull requests take the phase they serve, not a
  separate category.
- **gh.exe is not on PATH**; call it by full path:
  `%LOCALAPPDATA%\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe`.
- **Branching and merging**: branch from `main` for each piece of work, open a pull request,
  and merge with a merge commit so the pinned CAD ancestry is retained. `main` is protected;
  never force-push it or bypass its checks. Do not rename branches after merge.
- **Attribution**: commit messages and pull request descriptions carry no tool attribution
  or co-author lines anywhere. `docs/PROGRESS.md` and `docs/DECISIONS.md` describe work and
  decisions, not the tooling that produced them.
- **Decisions**: consequential choices are proposed first and written to `docs/DECISIONS.md`
  only after the researcher confirms them. Commands, results and blockers go to
  `docs/PROGRESS.md`.
- **Colab**: nothing runs in Colab without an exact reviewed commit and explicit
  authorisation; the bounded smoke gate has its own standing instruction recorded in
  `docs/COLAB_RUNBOOK.md`. Code is never edited or pushed from Colab.
- **Local checks**: `.venv\Scripts\python.exe -m pytest -q` and
  `.venv\Scripts\python.exe -m ruff check .` from the repository root before every push.

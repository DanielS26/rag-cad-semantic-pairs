# Repository conventions for coding agents

Read `docs/project-plan/COMPSCI764_Project_Implementation_Handoff.md` Section 1 before
changing anything; it is the authoritative brief. The conventions below repeat the ones that
apply to every change.

- **Pull request titles** start with the phase the work belongs to, in exactly the form
  `Phase N: <short description>` (capital P, space, phase number from handoff Section 10,
  colon, space). Documentation-only pull requests use the phase whose work they record.
- **Branching and merging**: branch from `main` for each piece of work, open a pull request,
  and merge with a merge commit so the pinned CAD ancestry is retained. `main` is protected;
  never force-push it or bypass its checks.
- **Attribution**: commit messages and pull request descriptions carry no tool attribution
  lines or footers. `docs/PROGRESS.md` and `docs/DECISIONS.md` describe work and decisions,
  not the tooling that produced them.
- **Decisions**: consequential choices are proposed first and written to `docs/DECISIONS.md`
  only after the researcher confirms them. Commands, results and blockers go to
  `docs/PROGRESS.md`.
- **Colab**: nothing runs in Colab without an exact reviewed commit and explicit
  authorisation; the bounded smoke gate has its own standing instruction recorded in
  `docs/COLAB_RUNBOOK.md`. Code is never edited or pushed from Colab.
- **Local checks**: `.venv\Scripts\python.exe -m pytest -q` and
  `.venv\Scripts\python.exe -m ruff check .` from the repository root before every push.

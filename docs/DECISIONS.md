# Confirmed Project Decisions

Consequential entries require explicit researcher confirmation before writing.
Propose the exact wording, reason, evidence, alternatives, and consequences first.
Never silently rewrite or delete an earlier entry; append a linked superseding
entry when an approved decision changes. Routine commands and results belong in
[PROGRESS.md](PROGRESS.md), not in this log.

The entries below record researcher approvals from 21 September 2026. Where the
older planning documents conflict with these explicit approvals, these entries
record the approved correction. This is not Phase 1A implementation authorisation.

## Entry Template

```markdown
## D-YYYYMMDD-NN - Short descriptive title

- Status: Confirmed | Superseded
- Date:
- Project phase:
- Category: Scientific | Data | Manual labelling | Implementation | Evaluation | Reporting
- Decision or important note:
- Context and reason:
- Evidence:
- Alternatives considered:
- Consequences for implementation/evaluation/report:
- Approved by:
- Related files, commands, results, correspondence, or commit:
- Supersedes / superseded by: None
```

## D-20260921-01 - Local documentation baseline and authorised history rewrite

- Status: Superseded
- Date: 2026-09-21
- Project phase: Repository preparation before Phase 1A
- Category: Implementation
- Decision or important note: "rewrite published history, treat my local as the good one, and open a branch to commit and push to remote main. My goal is to sync up what I have in local now with remote as well as in the future"
- Context and reason: The repository was initialised with documentation only. The researcher has relocated the planning files into docs/project-plan and explicitly selected a local-authoritative rewrite instead of the proposed history-preserving integration.
- Evidence: Local main and live origin/main both pointed to 7c8754585f0f3b713aff4bf6c66d96b0baf9d229 before this operation. Git status showed seven deleted old planning paths and seven untracked replacement paths.
- Alternatives considered: Preserve the initial commit and add a relocation commit; integrate pinned CAD history as originally proposed; rewrite the documentation baseline as requested.
- Consequences for implementation/evaluation/report: Replace the initial documentation commit on sync-local-baseline-20260921 and publish the reviewed local snapshot to origin/main with an explicit expected-old-SHA force-with-lease. This operation does not import CAD, establish CAD ancestry, or authorise future automatic force pushes. Ordinary future synchronisation uses reviewed commits and normal pushes; concurrent remote changes must be checked, not silently discarded. Collaborators must be notified of the rewritten main history.
- Approved by: Daniel Song, explicit P1 instruction in the coding session on 2026-09-21.
- Related files, commands, results, correspondence, or commit: [Planning handoff](project-plan/COMPSCI764_Project_Implementation_Handoff.md), [PROGRESS.md](PROGRESS.md); original commit 7c8754585f0f3b713aff4bf6c66d96b0baf9d229; git status, git log --all, and git ls-remote --heads origin.
- Supersedes / superseded by: Superseded by D-20260921-07 for the history-rewrite/publication method. The local snapshot remains authoritative. The original instruction above is retained for audit.

## D-20260921-02 - CPU implementation and candidate versus tested environment gates

- Status: Confirmed
- Date: 2026-09-21
- Project phase: Phase 1A, Phase 1B, and final execution gates
- Category: Implementation
- Decision or important note: The following researcher-supplied wording is approved in full.

> Phase 1A remains CPU-only. It must implement and CPU/fake-test the interfaces and commands required for Phase 1B, but it must not download or load Jina, download the official CAD artefacts, use a GPU, mount Drive, or execute the real smoke test.
>
> Phase 1B may run only with an explicitly reviewed and approved candidate environment profile. Candidate profiles may be used only for bounded smoke and conformance work. A candidate becomes a tested environment profile only after all Phase 1B Run A and Run B acceptance checks pass and the resulting dependency lock and profile are reviewed and committed.
>
> Final feature generation, full training and final evaluation must reject candidate or unknown profiles and require an exact tested-profile match.
>
> If required smoke implementation is found missing after Phase 1A review, stop and request a bounded CPU-only corrective authorisation before Phase 1B. Do not change or push project code from Colab.

- Context and reason: The original plan required a tested profile before the smoke that establishes it, and placed some smoke prerequisites in later implementation phases.
- Evidence: [Handoff](project-plan/COMPSCI764_Project_Implementation_Handoff.md), Sections 9.1 and 10; [Hybrid runbook](project-plan/COMPSCI764_Hybrid_Execution_Runbook.md), Sections 7, 10, and 11; researcher's explicit P2 wording on 2026-09-21.
- Alternatives considered: Reject every candidate profile, which blocks the first smoke; defer missing implementation until Colab, which violates the source-control contract; implement and fake-test prerequisites locally with separate candidate-only smoke permission.
- Consequences for implementation/evaluation/report: Apply stage-specific fail-closed gates and test both allowed and rejected profile states. Keep real execution separate from CPU implementation. Do not call a profile tested on Run A alone. The approved wording corrects conflicting phase-order and preflight statements in the older planning documents without relaxing any final-run requirement.
- Approved by: Daniel Song, explicit P2 decision in the coding session on 2026-09-21.
- Related files, commands, results, correspondence, or commit: [Start prompt](project-plan/COMPSCI764_Coding_Agent_Start_Prompt.md), [Handoff](project-plan/COMPSCI764_Project_Implementation_Handoff.md), [Hybrid runbook](project-plan/COMPSCI764_Hybrid_Execution_Runbook.md).
- Supersedes / superseded by: None.

## D-20260921-03 - Adopt released original CAD training data as D0

- Status: Confirmed
- Date: 2026-09-21
- Project phase: Release validation and Phase 4 adaptation
- Category: Data
- Decision or important note: After checksum/schema/licence validation and project-schema adaptation, use training_data_original at CAD-data revision f5efab920d61f8f37fa17260b71b770bf91ab79b as the common upstream D0 component for M0-M3.
- Context and reason: The official release removes the need to reconstruct the base dataset from the paper.
- Evidence: Supplied [CAD release audit](project-plan/COMPSCI764_CAD_Release_Audit_2026-09-19.md), Sections 2, 3, and 8 Proposal A. The audit reports 1,080 training records, 24,665 sentence rows, 1,625 malicious rows, and 23,040 benign rows; these were not independently revalidated in this session.
- Alternatives considered: Reconstruct D0; silently substitute or combine other released pools; use the pinned original training release after validation.
- Consequences for implementation/evaluation/report: Preserve an immutable source manifest and prove adaptation counts. Do not mix paraphrases or released test data into D0. This approval does not choose D0 holdout policy, split proportions, or authorise downloads now.
- Approved by: Daniel Song, explicit clarification "Yes, approve all four A-D" in the coding session on 2026-09-21.
- Related files, commands, results, correspondence, or commit: [CAD release audit Proposal A](project-plan/COMPSCI764_CAD_Release_Audit_2026-09-19.md), [Handoff](project-plan/COMPSCI764_Project_Implementation_Handoff.md).
- Supersedes / superseded by: None.

## D-20260921-04 - Released checkpoint is an upstream reference only

- Status: Confirmed
- Date: 2026-09-21
- Project phase: Phase 1B compatibility smoke and subsequent training
- Category: Evaluation
- Decision or important note: Use classifier_fullcad.pt at CAD-models revision 550e8cf87ebf33adf6ef83e56b24629d876e0512 for loading/filter/integration smoke tests and an upstream reference result. Train all primary M0-M3 checkpoints under the frozen project environment and seeds.
- Context and reason: The released checkpoint lacks seed and encoder-revision provenance, while the controlled study requires equal multi-seed training.
- Evidence: Supplied [CAD release audit](project-plan/COMPSCI764_CAD_Release_Audit_2026-09-19.md), Sections 3.4 and 8 Proposal B; live safe loading and real score compatibility remain unverified.
- Alternatives considered: Substitute the released head for a project condition; use it only as a labelled upstream reference while training all project conditions afresh.
- Consequences for implementation/evaluation/report: Do not compare an unknown-provenance checkpoint as though it were a newly trained equal-seed condition. Verify the expected hash and metadata before safe loading. Compatibility alone does not prove paper-score reproduction; M0 remains a smaller-data diagnostic.
- Approved by: Daniel Song, explicit clarification "Yes, approve all four A-D" in the coding session on 2026-09-21.
- Related files, commands, results, correspondence, or commit: [CAD release audit Proposal B](project-plan/COMPSCI764_CAD_Release_Audit_2026-09-19.md), [Hybrid runbook](project-plan/COMPSCI764_Hybrid_Execution_Runbook.md).
- Supersedes / superseded by: None.

## D-20260921-05 - Retain representation conformance and freeze gate

- Status: Confirmed
- Date: 2026-09-21
- Project phase: CAD representation conformance before final features
- Category: Scientific
- Decision or important note: Keep both paper_exact and repo_compatible implementations until the author clarifies checkpoint provenance; do not generate final features before one mode is approved and frozen.
- Context and reason: Released weights do not resolve the contextual-representation difference between the paper description and repository code.
- Evidence: Supplied [CAD release audit](project-plan/COMPSCI764_CAD_Release_Audit_2026-09-19.md), Sections 4, 7, and 8 Proposal C; [Handoff](project-plan/COMPSCI764_Project_Implementation_Handoff.md), Section 5.5.
- Alternatives considered: Assume paper/repository equivalence; automatically choose repo_compatible from checkpoint availability; retain both interpretations for bounded conformance checks and researcher selection.
- Consequences for implementation/evaluation/report: Test both interpretations using deterministic fake encoders and later approved bounded real checks. Record author clarification or its absence. This entry does not select a primary representation or authorise real encoder execution.
- Approved by: Daniel Song, explicit clarification "Yes, approve all four A-D" in the coding session on 2026-09-21.
- Related files, commands, results, correspondence, or commit: [CAD release audit Proposal C](project-plan/COMPSCI764_CAD_Release_Audit_2026-09-19.md), [Implementation map](project-plan/COMPSCI764_Full_Project_Implementation_Map.mmd).
- Supersedes / superseded by: None.

## D-20260921-06 - Normalize release schema while preserving source provenance

- Status: Confirmed
- Date: 2026-09-21
- Project phase: CPU validator implementation and later release adaptation
- Category: Data
- Decision or important note: Derive authoritative unit counts from numbered sentence_segments, record missing/mismatched supplied total_units, normalize optional paraphrase path prefixes in project metadata, retain all raw values, and record every transformation in an adaptation manifest.
- Context and reason: Documented schema variations would otherwise break strict loaders or source linking.
- Evidence: Supplied [CAD release audit](project-plan/COMPSCI764_CAD_Release_Audit_2026-09-19.md), Sections 3.3 and 8 Proposal D, reports missing banking counts, 1,278 stale supplied paraphrase counts, and two paraphrase source-path formats.
- Alternatives considered: Trust supplied total_units; rewrite upstream JSON in place; normalize derived metadata with explicit audit records while preserving sources.
- Consequences for implementation/evaluation/report: Keep upstream archives unchanged. Require supplied original train/test counts to match; explicitly report documented paraphrase mismatches. Retain raw and normalized paths. Use tiny synthetic fixtures for CPU tests; adapting the real release remains a separately authorised stage.
- Approved by: Daniel Song, explicit clarification "Yes, approve all four A-D" in the coding session on 2026-09-21.
- Related files, commands, results, correspondence, or commit: [CAD release audit Proposal D](project-plan/COMPSCI764_CAD_Release_Audit_2026-09-19.md), [Handoff](project-plan/COMPSCI764_Project_Implementation_Handoff.md).
- Supersedes / superseded by: None.

## D-20260921-07 - Preserve protected main and synchronise through a pull request

- Status: Confirmed
- Date: 2026-09-21
- Project phase: Repository preparation before Phase 1A
- Category: Implementation
- Decision or important note: Keep protections; use a normal commit and PR. Preserve the original published commit while bringing the current local documentation snapshot to main through the required pull-request workflow.
- Context and reason: GitHub rejected the authorised atomic history rewrite because main prohibits force pushes and requires pull requests. The researcher selected the protected normal-commit/PR alternative instead of arranging a rule exception.
- Evidence: GitHub returned GH013 with "Cannot force-push to this branch" and "Changes must be made through a pull request." The atomic push rejected both main and the new sync branch. The researcher then explicitly selected "Keep protections; use a normal commit and PR".
- Alternatives considered: Obtain an administrator-approved exception for the rewrite; preserve protections and submit a normal successor commit and PR. The researcher selected the latter.
- Consequences for implementation/evaluation/report: Keep origin/main history intact, preserve all local file contents, and publish sync-local-baseline-20260921 as a descendant of 7c8754585f0f3b713aff4bf6c66d96b0baf9d229. Open a PR targeting main and respect its review/merge requirements. Do not bypass rules, force-push main, or describe an unmerged branch as synchronised main. Future syncs use ordinary commits, branch pushes, and reviewed PRs, not automatic overwrites. CAD upstream integration remains unresolved.
- Approved by: Daniel Song, explicit protected-main clarification in the coding session on 2026-09-21.
- Related files, commands, results, correspondence, or commit: [PROGRESS.md](PROGRESS.md); D-20260921-01; rejected local-only root commit ce3c0452c15dcc1100cf588b7bfd13bbe1a334c9.
- Supersedes / superseded by: Supersedes D-20260921-01 for the history-rewrite/publication method.

## D-20260921-08 - Integrate pinned CAD history without rewriting main

- Status: Confirmed
- Date: 2026-09-21
- Project phase: Phase 1A foundation
- Category: Implementation
- Decision or important note: Integrate CAD commit 26e38a67f0a9e1de4cb3a876e4b021900a5d1c27 on a Phase 1A task branch through a history-preserving merge. Keep existing project history and documents, retain CAD as upstream, and verify imported upstream source remains unchanged. Submit changes through the protected-main PR workflow.
- Context and reason: The project already has published documentation history, so the original empty-directory clone procedure no longer applies.
- Evidence: GitHub API verified the exact CAD commit; current main is 0379a810d85ffdb559330bbc4b5f6baad5ea6d13. Main rules require PRs and prohibit force pushes, but do not require linear history.
- Alternatives considered: A pinned source snapshot without CAD ancestry; a history-preserving integration retaining both histories. The researcher selected the latter.
- Consequences for implementation/evaluation/report: Verify CAD ancestry and unchanged upstream source instead of claiming the initial project commit was the CAD commit. Preserve upstream licences. Review project-owned packaging and root configuration additions explicitly. No model/data release downloads, real smoke execution, or experiment-setting changes are authorised by this integration.
- Approved by: Daniel Song, explicit answer "Approve history-preserving CAD integration" on 2026-09-21.
- Related files, commands, results, correspondence, or commit: [Handoff](project-plan/COMPSCI764_Project_Implementation_Handoff.md), [PROGRESS.md](PROGRESS.md); D-20260921-07; GitHub commit and branch-rules API checks.
- Supersedes / superseded by: None. Resolves the upstream-integration question left open in D-20260921-07.

## D-20260921-09 - Approve bounded Phase 1B smoke candidate

- Status: Confirmed
- Date: 2026-09-21
- Project phase: Phase 1B smoke candidate approval
- Category: Implementation
- Decision or important note: Daniel Song approves the candidate from `7830d588715cc8e607847ca93dec8ccdebabf2bc` for bounded smoke testing only, under the existing licence, download, security, and shared 20-unit/three-hour limits.
- Context and reason: Explicit researcher approval and passing regression tests.
- Evidence: Daniel Song's explicit approval of the proposed entry exactly as written; [PR #5](https://github.com/DanielS26/rag-cad-semantic-pairs/pull/5); passing Windows, Ubuntu, and candidate-Linux [CI](https://github.com/DanielS26/rag-cad-semantic-pairs/actions/runs/35555877836) at 6f73c34dfa3f4389b42bd6a9e4e5b0b9ffca42dd.
- Alternatives considered: Leave smoke approval disabled.
- Consequences for implementation/evaluation/report: Permits smoke validation, not tested/final status.
- Approved by: Daniel Song, explicit confirmation to append the proposed entry on 2026-09-21.
- Related files, commands, results, correspondence, or commit: [Candidate profile](../configs/environments/colab_candidate.yaml), [approval regression tests](../tests/test_candidate_preparation.py), [preparation evidence](PHASE1B_PREPARATION.md); candidate base 7830d588715cc8e607847ca93dec8ccdebabf2bc; approval commit 6f73c34dfa3f4389b42bd6a9e4e5b0b9ffca42dd; D-20260921-02.
- Supersedes / superseded by: None.
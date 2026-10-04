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
## D-20260921-10 - Isolate the Colab candidate environment in a virtual environment

- Status: Confirmed
- Date: 2026-09-21
- Project phase: Phase 1B bootstrap correction before Run A
- Category: Implementation
- Decision or important note: The Phase 1B bootstrap installs the committed candidate lock into a dedicated virtual environment inside the Colab runtime, and every dependency check, test, preflight and project CLI command runs with that environment's interpreter rather than Colab's system Python.
- Context and reason: Run A on ffabf8369c18d162bee2cb8ea49e563f90501b6a reached the pip_check stage and failed only because of Google-preinstalled packages, including one conflict (missing jedi for ipython) that exists before any project install. The system interpreter cannot satisfy the gate, and the candidate-linux CI job already validates the lock in an isolated environment.
- Evidence: The eight-line `pip check` output from that attempt named only preinstalled Colab packages (ipython, google-colab, diffusers, datasets, gcsfs, gradio, cuda-python, torchvision) conflicting with the lock's requests, huggingface-hub, fsspec, cuda-bindings and torch pins; passing candidate-linux CI on the same lock at the same commit.
- Alternatives considered: Relax or scope pip check, which weakens the gate; re-pin to Colab's preinstalled versions, which abandons the paper's environment and drifts with Google's image.
- Consequences for implementation/evaluation/report: No pin, lock, profile, budget or scientific change. The recorded environment fingerprint describes the isolated environment. The change requires a reviewed PR, a new bootstrap hash and fresh execution authorisation.
- Approved by: Daniel Song, explicit "I authorise" for the proposed entry in the coding session on 2026-09-21.
- Related files, commands, results, correspondence, or commit: [Bootstrap helper](../scripts/bootstrap_colab.py), [runner notebook](../notebooks/COMPSCI764_Colab_Runner.ipynb), [bootstrap tests](../tests/test_colab_bootstrap.py), [Colab runbook](COLAB_RUNBOOK.md), [PROGRESS.md](PROGRESS.md); failed attempt from ffabf8369c18d162bee2cb8ea49e563f90501b6a; D-20260921-02; D-20260921-09.
- Supersedes / superseded by: None.

## D-20260921-11 - Re-target the Phase 1B candidate environment to Python 3.13

- Status: Confirmed
- Date: 2026-09-21
- Project phase: Phase 1B bootstrap correction before Run A
- Category: Implementation
- Decision or important note: The candidate lock, CPU evidence and preflight Python rule move from 3.12.x to 3.13.x, regenerated by the existing Ubuntu lock CI job and installed/tested there before use.
- Context and reason: Colab's runtime now ships Python 3.13.15 without a 3.12 interpreter, and the candidate gate correctly rejects the mismatch. Colab's Python build also lacks ensurepip, so the isolated environment is created without pip and the system pip installs the lock into it.
- Evidence: Diagnostic output from the 44dce5f300e9101913c07df1b45d3c1b1bd43836 attempt (`Python 3.13.15`, `/usr/local/bin/python`, `No module named 'ensurepip'`, no virtualenv or uv); the preceding attempt from ffabf8369c18d162bee2cb8ea49e563f90501b6a installed all pinned packages on Python 3.13 without error.
- Alternatives considered: Install Python 3.12 inside Colab through uv, deadsnakes or conda (new unaudited external download, slower and fragile bootstrap); use Colab's temporary fallback runtime (short-lived, unsuitable for a tested profile).
- Consequences for implementation/evaluation/report: All package pins, model pins, representation, tolerances and budget unchanged unless re-resolution forces a change, which is reported before merge. The final report records Python 3.13 as a deviation from the paper's stated 3.12.3. Tested-profile status still requires Run A and Run B. The Windows development environment remains Python 3.12.
- Approved by: Daniel Song, "ok go with option A" after the recommendation and proposed entry in the coding session on 2026-09-21.
- Related files, commands, results, correspondence, or commit: [Candidate lock workflow](../.github/workflows/candidate-lock.yml), [CPU tests workflow](../.github/workflows/cpu-tests.yml), [profile validation](../src/rag_cad/config.py), [candidate lock](../requirements/colab-core.candidate.lock.txt), [CPU evidence](../configs/environments/colab_candidate_cpu_evidence.json), [candidate profile](../configs/environments/colab_candidate.yaml), [bootstrap helper](../scripts/bootstrap_colab.py), [PROGRESS.md](PROGRESS.md); D-20260921-09; D-20260921-10.
- Supersedes / superseded by: Supersedes the Python 3.12.x candidate constraint recorded with D-20260921-09; the smoke approval itself remains in force.

## D-20260922-12 - Freeze the tested Colab environment profile from Run A and Run B

- Status: Confirmed
- Date: 2026-09-22
- Project phase: Phase 1B freeze after the live smoke gate
- Category: Implementation
- Decision or important note: The candidate environment is promoted to tested as configs/environments/colab_tested.yaml with lock requirements/colab-core.lock.txt (SHA-256 1b270c043e4cbe273dd7c5e67b6f720bd9ec18a2b105ffcc83a7900d746f11e9), reviewed commit a822b9a032fc3d6c27261b25c62363fc3bc88142, Run A manifest 901cee9ae56cf91d89d1df50abb5ac29f481c20f893edc4bc8423dd608cdad2b and Run B manifest 05d322135aa734960d48d2a496f9a21f9b0b14d21d885836a96448433c9cb621. Final feature, training and evaluation stages may use only this profile, and only after a separate compute-budget approval.
- Context and reason: Run A completed every Phase 1B check in one fresh NVIDIA L4 runtime (Python 3.13.15, CUDA 12.8, driver 580.82.07) and published a verified artefact; Run B restored it in a second fresh runtime with an identical environment fingerprint (environment ID aed3f42347ddf55ec9c0b310865300b9b7dc90f99b151b71124ea0d1716296c1) and matching predictions.
- Evidence: Run A report and Run B report published on Drive under run IDs 20260921T231238Z_a822b9a0_smoke_5bd0f99b and 20260921T232747Z_a822b9a0_smoke-run-b_5bd0f99b; the Run A manifest hash is the value Run B recorded as its parent; the Run B manifest hash is the `_SUCCESS` content read from Drive by Daniel Song; progress entries for both runs; post-merge CI on a822b9a0.
- Alternatives considered: Keep the profile as candidate and repeat the gate before every stage (wasteful); promote without Run B (violates D-20260921-02).
- Consequences for implementation/evaluation/report: Any change to src/rag_cad or scripts/bootstrap_colab.py after a822b9a0 invalidates the profile for final stages until the gate is rerun. The representation value is the smoke value; a different primary representation under D-20260921-05 requires rerunning the gate in that mode. Python 3.13 and sentencepiece 0.2.1 remain recorded deviations from the paper's environment. compute_budget_approved is false until a bounded final-stage budget is approved separately.
- Approved by: Daniel Song, "I approved the decision log" after the proposed entry in the coding session on 2026-09-22.
- Related files, commands, results, correspondence, or commit: [Tested profile](../configs/environments/colab_tested.yaml), [tested lock](../requirements/colab-core.lock.txt), [candidate profile](../configs/environments/colab_candidate.yaml), [tests](../tests/test_candidate_preparation.py), [PROGRESS.md](PROGRESS.md); D-20260921-02; D-20260921-05; D-20260921-09; D-20260921-10; D-20260921-11.
- Supersedes / superseded by: None. Completes the candidate-to-tested transition defined in D-20260921-02.

## D-20261004-13 - Select repo_compatible as the primary representation

- Status: Confirmed
- Date: 2026-10-04
- Project phase: Phase 4A, representation decision before final feature builds
- Category: Scientific
- Decision or important note: repo_compatible is the primary representation for every project feature build and for runtime scoring (M0 to M3, N0 and the RAG filter). paper_exact stays implemented and documented as a secondary variant for a bounded robustness check only; it produces no primary result. configs/experiment.yaml now sets representation: repo_compatible.
- Context and reason: No sentence-level oracle is published for the base detector, so the training recipe of the released checkpoint cannot be identified by reproducing a number. The released-test fit test on all 389 records shows the released checkpoint behaves the same under both recipes (three of 9,776 decisions, one detection and 0.0003 masked AUPRC apart), which the pooling arithmetic explains: the recipes differ only by a sentence's own share of the passage mean. repo_compatible is the computation the released code performs (detector/defense.py and build_embeddings.py), so it is the most likely origin of the released checkpoint and of the paper's agent-level results, and it keeps the project's features row-for-row comparable with the upstream pipeline. Proposed on 2026-09-24 after the full run; no author clarification had arrived.
- Evidence: Full-run report and predictions under artefacts/conformance/20260923T080927Z_d0b92eeb_released-test-full_5bd0f99b (predictions SHA-256 3a727361...); pilot report under artefacts/conformance/20260923T060056Z_f4181bc8_released-test-pilot_5bd0f99b; Run A representation_modes evidence from 0cc9ad77; [REPRESENTATION_MODES.md](REPRESENTATION_MODES.md); progress entries of 2026-09-22, 2026-09-23 and 2026-09-24.
- Alternatives considered: paper_exact (matches the paper's description; higher masked AUPRC by one row; not the released computation). Deferring until the authors reply (blocks Phase 4 indefinitely; a reply can still supersede this entry).
- Consequences for implementation/evaluation/report: Final feature builds use repo_compatible through RepresentationConfig, whose representation_id binds every shard and checkpoint to it. The smoke gate (Run A and a fresh-runtime Run B) is rerun in this mode at the commit from which the first final-stage run is launched, which freezes the tested profile for it as D-20260922-12 requires; it is not rerun earlier, because any later code change would invalidate the profile again. The report states the choice, the fit-test result and the arithmetic reason, and gives the released checkpoint's reference numbers on the released test set with the no-oracle caveat. If an author reply contradicts the choice, a superseding entry is required and any features built under this one are rebuilt.
- Approved by: Daniel Song, "yes go with that" to the proposed entry in the coding session on 2026-10-04.
- Related files, commands, results, correspondence, or commit: [REPRESENTATION_MODES.md](REPRESENTATION_MODES.md), [experiment.yaml](../configs/experiment.yaml), [candidate profile](../configs/environments/colab_candidate.yaml), [representation module](../src/rag_cad/cad/representation.py), [PROGRESS.md](PROGRESS.md); D-20260921-05; D-20260922-12.
- Supersedes / superseded by: Completes D-20260921-05, which kept both modes and selected none.

## D-20261004-14 - Implementation choices of Phases 2 to 4A, recorded in one entry

- Status: Confirmed
- Date: 2026-10-04
- Project phase: Phases 2, 3 and 4A
- Category: Implementation
- Decision or important note: The following choices, made while implementing the data contracts, the feature builder, the generic scorer and the released-test stage, are confirmed as they stand:
  1. Unresolved experiment values refuse execution: a null value in configs/experiment.yaml (split ratios, near-duplicate threshold, benign length tolerance, augmentation budget, D0 holdout policy, shared-malicious approval) stops the command that needs it instead of falling back to a default.
  2. Raw dataset records carry split null; splits exist only in a deterministic group-level manifest (seeded SHA-256 order over group IDs, deficit fill, released CAD test records pinned to test) bound to the dataset content digest.
  3. Leakage rule: families, groups, exact duplicate records, and exact or near-duplicate target sentences may not cross splits; benign context overlap across splits is reported but not refused.
  4. Near-duplicate definition: normalised word 3-shingle Jaccard similarity computed exactly over all candidate pairs; the threshold stays an experiment value.
  5. Equal-budget rule: conditions must have identical record counts, identical shared pools, complete augmentation units with equal sentence counts, and benign-to-malicious length ratios within the experiment tolerance.
  6. Feature storage: content-addressed shards of 256 records per pool (base, shared malicious, the three benign pools, common validation and test) holding features.npz (X float32 [N, 2048], y int64), rows.jsonl with the row identity fields, and manifest.json; a shard is reused only after its identity and ordered record hashes verify; a root claimed by another identity is refused; conditions are assembled by (record_id, sentence_id) so M1 to M3 share byte-identical D0 and malicious rows. The shard size may change once before the final feature manifest is frozen.
  7. representation_id is the digest of mode, encoder weights revision, encoder code revision, segmenter identity, dtype and attention; training features and runtime scoring build through the same RepresentationConfig.
  8. Scoring contract: the threshold is fixed at 0.5 and the passage filter removes sentences strictly above it; a scorer with any other threshold is refused; evidence records retained and removed text.
  9. Inputs longer than the encoder's 8,192 tokens are refused and listed, never truncated as the upstream builder does.
  10. The upstream boundary-masked evaluator (the first three and last five sentences of each injection span dropped, pred = prob >= 0.5) is implemented beside the project's all-rows evaluator (pred = prob > 0.5), and both are reported.
  11. The released-test fit test on the authors' test set is the method for the representation decision, run as a conformance stage under the candidate profile with a ten-record pilot before the full run; its domain is the first directory under the extracted test folder, as upstream defines it, and both modes are built from one set of encoder passes.
  12. Bounded released-test (conformance) runs draw on the same connected-time and compute-unit cap as the smoke attempts, carried forward across runs.
  13. The Run A smoke stage includes a two-mode comparison on its synthetic sample as standing evidence.
- Context and reason: Each choice keeps the pipeline deterministic, auditable and refusing by default. Each was recorded in docs/PROGRESS.md when made (entries of 2026-09-22, 2026-09-23 and 2026-09-24) and listed as a decision-log candidate; Daniel Song asked for one batched entry rather than one entry per choice.
- Evidence: The progress entries named above; the tests under tests/ that pin each behaviour (data schema, segmentation round trip, family leakage, equal budget, feature metadata alignment, RAG filter, detector metrics, released test, conformance CLI).
- Alternatives considered: One entry per choice (more bookkeeping for choices that are already tested and logged); leaving them in the progress log only (harder to find when the report is written).
- Consequences for implementation/evaluation/report: Changing any of these later needs a superseding entry. The report's methods section can cite this entry for the data, feature and evaluation contracts.
- Approved by: Daniel Song, "give them a one batched entry" in the coding session on 2026-10-04.
- Related files, commands, results, correspondence, or commit: [PROGRESS.md](PROGRESS.md), [experiment.yaml](../configs/experiment.yaml), [data package](../src/rag_cad/data/), [feature store](../src/rag_cad/cad/feature_store.py), [feature builder](../src/rag_cad/cad/feature_builder.py), [scorer](../src/rag_cad/cad/scorer.py), [detector metrics](../src/rag_cad/evaluation/detector_metrics.py), [released test](../src/rag_cad/operations/released_test.py); D-20260921-05; D-20260922-12; D-20261004-13.
- Supersedes / superseded by: None.

## D-20261004-15 - Experiment values for family splits, leakage checks and equal budgets

- Status: Confirmed
- Date: 2026-10-04
- Project phase: Phase 0 scientific contract, applied in Phases 5 and 6
- Category: Scientific
- Decision or important note: configs/experiment.yaml now sets: split_ratios train 0.7, validation 0.15, test 0.15, applied to whole leakage groups (families) with released CAD test records pinned to test; d0_holdout_policy none, meaning every official D0 training record trains, the released CAD test set is the upstream reference test only, and the held-out project families form the project's test; near_duplicate_threshold 0.8 (normalised word 3-shingle Jaccard); benign_length_tolerance 0.25 (the longest unit in a benign-malicious pair may exceed the shortest by at most 25 per cent of characters); shared_malicious_additions true (M1 to M3 share the same malicious additions and differ only in their benign half). augmentation_budget_sentence_rows stays null, deliberately, until the 30 to 50 family pilot measures how many rows a family yields; the commands that need it keep refusing until a superseding entry sets it. The former shared_malicious_tutor_approval flag is removed, because tutor approval is not a gate in this project (D-20261004-16); shared_malicious_additions true is the team's decision (handoff Section 14, question 9).
- Context and reason: The number of held-out families matters more than the percentage: each test family contributes one malicious sentence and its benign twins, so a test share of 10 per cent of a few hundred hand-written families leaves too few sentences to separate M1, M2 and M3 from noise, while training is dominated by D0's 24,665 rows and loses little. 70/15/15 gives 30 test families from 200 and 60 from 400. The near-duplicate threshold and the length tolerance are the values the Phase 2 fixtures already satisfy and that catch rewordings and padding without refusing legitimate pairs. Sharing the malicious additions is what isolates the benign-counterpart effect the project tests. Suggested defaults were presented with these reasons and approved.
- Evidence: [Handoff](project-plan/COMPSCI764_Project_Implementation_Handoff.md) Phase 0 checklist and Section 14 questions 3, 4 and 9; Phase 2 implementation and tests (tests/test_family_leakage.py, tests/test_equal_budget.py, tests/test_data_cli.py); progress entry of 2026-10-04.
- Alternatives considered: 80/10/10 (adequate only once the family count is large, roughly 500 or more); k-fold rotation over families (cheap to train because features never change with the split, but needs pipeline work; to be adopted if the family count stays small); holding out part of D0 (reduces the base training data without adding a test the project needs); a stricter near-duplicate threshold such as 0.6 (would refuse legitimate minimal pairs that share most of their words by design).
- Consequences for implementation/evaluation/report: data split, data check-leakage and data compare-budgets run with these values from the first family batch; the split manifest records the ratios and seed 764. If the final family count gives fewer than about 40 test families, a superseding entry revisits the ratio or adopts k-fold. The augmentation budget is the one remaining null, with its named trigger. The report states the ratios, thresholds and the sharing design with the reasons above.
- Approved by: Daniel Song, "I like your default suggestions for question 3 above, go with them" in the coding session on 2026-10-04.
- Related files, commands, results, correspondence, or commit: [experiment.yaml](../configs/experiment.yaml), [split module](../src/rag_cad/data/split.py), [conditions module](../src/rag_cad/data/conditions.py), [data commands](../src/rag_cad/data/commands.py), [DATA_CARD.md](DATA_CARD.md), [PROGRESS.md](PROGRESS.md); D-20261004-14 (items 1 to 5).
- Supersedes / superseded by: None.

## D-20261004-16 - Decision authority rests with the researchers; tutor approval is not a gate

- Status: Confirmed
- Date: 2026-10-04
- Project phase: All phases
- Category: Process
- Decision or important note: Decisions in this project are made by the two researchers, Daniel Song and Daniel Oliver. The tutor advises but does not give final approval, so no step, flag or checklist item waits for tutor approval. A decision is acceptable when it is reasonable, explainable and practical, and it is recorded in this log with its reasons. Tutor feedback is an input that may prompt a superseding entry.
- Context and reason: The handoff, written before the working arrangement was clear, made the tutor the approver of several items (augmentation size and split ratios, the shared-malicious design, the family pilot review, the representation decision), and the experiment configuration carried a shared_malicious_tutor_approval flag. Daniel Song clarified on 2026-10-04 that the tutor does not give final approval and that the decisions are the team's own.
- Evidence: Daniel Song's statement in the coding session on 2026-10-04; handoff Section 1 item 14, Section 14 and the Phase 0, 4A and 5 checklists as amended; CLAUDE.md.
- Alternatives considered: Keeping a tutor-approval flag as a formality (misstates who decides and blocks commands on a signature that will not come); dropping the review steps altogether (the reviews stay, performed by the researchers).
- Consequences for implementation/evaluation/report: The shared_malicious_tutor_approval flag is removed from configs/experiment.yaml; shared_malicious_additions true stands (D-20261004-15). Handoff wording that named the tutor as approver now names the researchers. The report describes the design choices as the team's, with the recorded reasons. Entries already merged are not edited; D-20261004-15, still in review, is amended before merge.
- Approved by: Daniel Song, "our tutor do not give final approval, it is mostly on us ... as long as they are reasonable and explainable and practical" in the coding session on 2026-10-04.
- Related files, commands, results, correspondence, or commit: [Handoff](project-plan/COMPSCI764_Project_Implementation_Handoff.md), [CLAUDE.md](../CLAUDE.md), [experiment.yaml](../configs/experiment.yaml), [PROGRESS.md](PROGRESS.md); D-20261004-13; D-20261004-15.
- Supersedes / superseded by: Amends the tutor-approval wording of D-20261004-15 before its merge; no other entry superseded.

## D-20261004-17 - Compute budget pools for the remaining GPU work

- Status: Confirmed
- Date: 2026-10-04
- Project phase: Phases 4 to 8
- Category: Implementation
- Decision or important note: Four budget pools replace the single smoke cap for all Colab work from 4 October 2026 onward. Pool A, bounded gate and conformance runs: 6 connected hours and 12 compute units. Pool B, Phase 4 final stages (D0 features, M0 training and evaluation): 4 hours and 8 units. Pool C, Phases 5 and 6 (augmentation features, M1 to M3 training and evaluation): 6 hours and 12 units. Pool D, Phases 7 and 8 (harness scoring and the end-to-end comparison): 8 hours and 16 units. Total ceiling 24 hours and 48 units. Each pool is a hard cap carried forward in the notebook inputs of its stages; every run cuts itself off at the pool's remainder; an exhausted pool needs a new entry, never a quiet top-up. Usage before 4 October (7,200 s and 1.84 units under the old cap) is recorded history and is not charged to any pool. The LLM generator's API budget for Phases 7 and 8 is a separate decision.
- Context and reason: The measured cost is 41 ms per encoder pass on the L4 (full released-test run, 2026-09-23). From it, the remaining GPU work is estimated at about six hours in total: one hour of gate reruns, 1.5 hours for Phase 4, one to two hours for Phases 5 and 6, and 1.5 hours for Phases 7 and 8, where the encoder work is shared across heads. Daniel Song asked for a budget that is reasonable with enough buffer and delegated the figures; the pools are roughly four times the estimates and fit within one month of a Colab Pro allowance.
- Evidence: Progress entries of 2026-09-22 to 2026-10-04 (measured timings and usage); [COLAB_RUNBOOK.md](COLAB_RUNBOOK.md) budget section; D-20260921-09 (the original smoke cap).
- Alternatives considered: One undivided ceiling (loses the per-phase stop that catches a runaway stage); keeping the original 3-hour smoke cap and approving each final stage separately (more interruptions for no extra safety); budgets in units only (the unit rate varies by GPU, so connected time is the binding limit).
- Consequences for implementation/evaluation/report: The runner's cap constants become inputs set per pool when the Phase 4 stage is added; the tested profile's compute_budget_approved becomes true when the profile is next frozen, referencing this entry; the runbook's budget section is rewritten to the pools; the operator cadence (snapshot, run, disconnect and delete) is unchanged. Usage per run continues to be recorded in docs/PROGRESS.md against its pool.
- Approved by: Daniel Song, "set one for me that is reasonable with enough buffer" in the coding session on 2026-10-04; the figures were stated back in the same session before being recorded.
- Related files, commands, results, correspondence, or commit: [COLAB_RUNBOOK.md](COLAB_RUNBOOK.md), [candidate profile](../configs/environments/colab_candidate.yaml), [tested profile](../configs/environments/colab_tested.yaml), [runner notebook](../notebooks/COMPSCI764_Colab_Runner.ipynb), [PROGRESS.md](PROGRESS.md); D-20260921-09; D-20260922-12.
- Supersedes / superseded by: Supersedes the 20-unit / 10,800-second smoke cap of D-20260921-09 for runs from 4 October 2026; D-20260921-09 remains the record of the Phase 1B approval.

## D-20261004-18 - Re-freeze the tested Colab profile from the e7d45fc8 gate pass with the compute budget approved

- Status: Confirmed
- Date: 2026-10-04
- Project phase: Phase 4, gate rerun before the first final-stage run
- Category: Implementation
- Decision or important note: The tested profile configs/environments/colab_tested.yaml is re-issued from Run A and Run B of 4 October 2026: reviewed commit e7d45fc84464cbad027eeafc47bcb9a7f93754e6, lock requirements/colab-core.lock.txt (SHA-256 1b270c043e4cbe273dd7c5e67b6f720bd9ec18a2b105ffcc83a7900d746f11e9, unchanged), Run A manifest 32d91cae4056f3cbc223f08d09ef22e639a9e83fc92fac0e2cabc22ea686b5aa, Run B manifest d08ef5f3a9164356389e1e2213b453fa024546d482bf7a9a43bbb598618c994b, environment ID d95a1d816fd98cbde914a4491becd40cd6ae4e3fad7e60a94b164ba86a158614, representation repo_compatible. compute_budget_approved becomes true under the pools of D-20261004-17. Final stages (features, train, evaluate) may run under this profile from any commit that descends from e7d45fc8 without changes to src/rag_cad or scripts/bootstrap_colab.py.
- Context and reason: D-20260922-12 invalidates the tested profile on any code change, and D-20261004-13 requires the gate in the chosen mode at the commit from which the first final-stage run is launched. Phase 4 (pull requests #22 to #24) changed the code and the notebook inputs, so the gate was rerun on the merge commit under budget pool A. Run A completed all eighteen checks in a fresh NVIDIA L4 runtime (Python 3.13.15, CUDA 12.8, driver 580.82.07) and published a verified artefact; Run B restored it in a second fresh runtime with the identical fingerprint and matching predictions. Every measured value equals the a822b9a0 freeze apart from the commit-bound environment ID.
- Evidence: Run A and Run B reports published on Drive under run IDs 20261004T083811Z_e7d45fc8_smoke_fe6f6a3d and 20261004T083811Z_e7d45fc8_smoke-run-b_fe6f6a3d; the Run A manifest hash is the value Run B recorded as its parent; the Run B manifest hash is the `_SUCCESS` content read from Drive by Daniel Song; progress entry of 2026-10-04; post-merge CI on e7d45fc8.
- Alternatives considered: Keep the a822b9a0 profile (invalid, the code changed); run m0 under the candidate profile (final stages refuse it by design); add the planned leak-excluded released-test metric to the evaluator first and rerun the gate once more (another gate pass for a number that the published per-row predictions allow to be computed afterwards on CPU).
- Consequences for implementation/evaluation/report: The first m0 run launches from the merge commit of the freeze pull request, which changes only configs, docs and tests. Any later change to src/rag_cad or the bootstrap, including the leak-excluded metric, invalidates the profile again and needs another gate pass before the next final stage. Usage per run continues to be recorded in docs/PROGRESS.md against its pool.
- Approved by: Daniel Song, "approve D-20261004-18" in the coding session on 2026-10-04, after the proposed entry and the two orderings of the leak-excluded metric work were shown.
- Related files, commands, results, correspondence, or commit: [Tested profile](../configs/environments/colab_tested.yaml), [tested lock](../requirements/colab-core.lock.txt), [candidate profile](../configs/environments/colab_candidate.yaml), [tests](../tests/test_candidate_preparation.py), [PROGRESS.md](PROGRESS.md), [COLAB_RUNBOOK.md](COLAB_RUNBOOK.md); D-20260922-12; D-20261004-13; D-20261004-17.
- Supersedes / superseded by: Re-issues the profile frozen by D-20260922-12, whose invalidation rule remains in force; none superseded.

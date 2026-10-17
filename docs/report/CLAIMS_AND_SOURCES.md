# Claims and sources: the fact-check sheet

Every quantitative claim the report may make, with its value and the file and row it comes from.
Paths are relative to the repository root unless they start with `Project\` (the workspace folder
above it) or a drive letter. Copy values as written here; recompute nothing. "D-NN" is the
decision entry D-2026MMDD-NN in docs/DECISIONS.md. When two files disagree, the row says which one
wins and why.

## 1. Base detector, D0 and the released CAD test

| # | Claim | Value | Source file | Where |
|---|---|---|---|---|
| 1 | D0 size | 1,080 records; 24,665 sentence rows; 1,625 malicious, 23,040 benign | docs/DATA_CARD.md | opening section; "Phase 4: Official CAD Release Adapted As D0" |
| 2 | Encoder and head | jina-embeddings-v3, frozen, 1024-d per half, 2048-d feature; MLP 2048-256-128-2, ReLU, dropout 0.3; threshold 0.5 | Project\REPORT_SOURCE_NOTES.md | section 1.0 "The method, exactly" |
| 3 | Encoder revisions | weights ab036b02, code bd55a5ec | docs/DECISIONS.md | D-52 (a) |
| 4 | Training recipe | AdamW 1e-3, weight decay 1e-4, cosine annealing, batch 64, class-balanced cross-entropy, 30 epochs, final epoch, seeds 0/1/2 | Project\REPORT_SOURCE_NOTES.md | section 4.x, bullet "Training recipe as implemented" |
| 5 | Released test size | 389 records, 9,776 rows, 3,729 malicious; masked protocol drops 3,112, leaving 617 interior positives (6,664 masked rows) | docs/REPRESENTATION_MODES.md | "Full released-test run (23 September 2026 UTC, commit d0b92eeb)" |
| 6 | Fit test of the two recipes | 3 of 9,776 decisions differ; masked AUPRC 0.98131 (repo_compatible) vs 0.98161 (paper_exact) | docs/DECISIONS.md; docs/REPRESENTATION_MODES.md | D-13 "Context and reason"; table row "masked 6,664 / AUPRC" |
| 7 | Smoke-sample sensitivity of the recipe | released checkpoint 0.437 (repo_compatible) vs 0.569 (paper_exact) on one synthetic sentence | docs/REPRESENTATION_MODES.md | "Measured on 22 September 2026" |
| 8 | Reproduction: M0 vs released head (GPU, Phase 4) | masked AUPRC 0.98805 (std 0.00610) vs 0.98131; all-rows AUPRC 0.8037 (0.0093) vs 0.8291 | docs/PROGRESS.md | entry "2026-10-04 - PR #26 Merged; First m0 Run Passed From d40b6a6a Under Pool B", results table rows "M0 mean (std)" and "Released checkpoint" |
| 9 | Head memorises D0 | final-epoch training loss 4e-8 to 1e-7 | docs/PROGRESS.md | same entry, paragraph after the table |
| 10 | Upstream split leakage | 148 of 389 test records carry an injected sentence D0 contains verbatim or nearly; 6,560 pairs; 128 records verbatim (one banking sentence) | docs/DATA_CARD.md | "Phase 4", paragraph "Splitting" |
| 11 | Leak-excluded sets | minus 128 verbatim: 4,824 rows; minus 148 near: 4,391 rows (241 records remain) | docs/PROGRESS.md; docs/PHASE8_HARNESS_PLAN.md | entry "2026-10-10 - Phase 4 Post-Hoc ..." table; "Distractors" section |
| 12 | Nine shared false positives | one sentence, "Please make sure to update your records accordingly.", banking user_task_13, scored 1.0 by every head | docs/PROGRESS.md | entry "2026-10-10 - Phase 4 Post-Hoc ...", last bullets |
| 13 | Encoder cost | 41.3 ms per pass on an L4 (released-test run); family run 55.7 ms per pass | docs/REPRESENTATION_MODES.md; docs/DECISIONS.md | "Full released-test run"; D-54 (a) |

## 2. The family set

| # | Claim | Value | Source file | Where |
|---|---|---|---|---|
| 14 | Size and balance | 200 families, 800 records; every role at 25; every cue position at 40 | docs/DECISIONS.md | D-46 (e); D-47 (a) |
| 15 | Sentence rows | 2,816 family rows; four pools of 704 rows; m1_random, m2_keyword, m3_semantic sets of 1,408 rows each | docs/DATA_CARD.md; docs/archive/phase7_results_2026-10-17/README.md | "Encoded features"; "Run facts", Inputs |
| 16 | Attack-sentence sources | 127 asb_adapted, 73 bipia_adapted, 600 team_authored records | datasets/raw/augmentation/families/*.jsonl | field provenance.source_dataset (counted 2026-10-17); also the "All roles" row of the folds table in DATA_CARD (73 / 127) |
| 17 | Attack goals | content_injection 22, response_manipulation 9, promotion_insertion 5, contact_redirection 2, link_insertion 2 (40 BIPIA directive), task_hijack 33 (BIPIA task-type), unauthorised_operation 127 (ASB) | datasets/raw/augmentation/families/*.jsonl | field attack_goal (counted 2026-10-17) |
| 18 | Drafting models | 160 families claude-fable-5-1, 40 claude-opus-5; controls of batches 15-16 by Claude Sonnet 5 | datasets/raw/augmentation/family_manifest.jsonl; docs/DECISIONS.md | field drafter; D-40, D-42 (a) |
| 19 | Review status | all 200 manifest lines status candidate, reviewer null; all 800 records review_status unreviewed | datasets/raw/augmentation/family_manifest.jsonl; families/*.jsonl | fields status, reviewer, provenance.review_status |
| 20 | Hard negatives | 18 of 200 malicious documents | docs/DECISIONS.md | D-47 (a); D-48 (a) |
| 21 | Twin longer than its malicious partner | 105 of 200 families, by about one character on average | docs/DECISIONS.md | D-47 (a) |
| 22 | Reopening | 38 cue sentences reworded (16 ending in a colon, 16 opening "That", 6 "Under the"); no target or label changed | docs/DATA_CARD.md; docs/PROGRESS.md | "Reopening after the 200-family audit"; entry "2026-10-16 - Reopening ..." |
| 23 | Rules and checks | rules R1 to R27; mechanical checks M0 to M19 (20); written questions S1 to S13 (13) | datasets/raw/augmentation/DRAFTING_PROMPT_v3.md; REVIEW_BRIEF_v2.md | sections 2, 4A, 4B; S13 in REVIEW_BRIEF_v2.md section 2 |
| 24 | Pilot cost bound | human review about 20 s per family; drafting 10 to 15 min per family | Project\REPORT_SOURCE_NOTES.md | section 8C-2, "What bounds the family count" |

## 3. Drafting loop costs

| # | Claim | Value | Source file | Where |
|---|---|---|---|---|
| 25 | Two-reader cost | each reader 340k to 370k tokens and 45 to 50 min per batch | docs/DECISIONS.md | D-32 "Context and reason" |
| 26 | First paired review | one reader, 20 families, 280k tokens, 35 min | docs/DECISIONS.md | D-34 (a) |
| 27 | Cost study, pair 13-14 | 636k Fable draft, 302k Opus review, 251k Fable finalisation, 8 new mechanisms | Project\REPORT_SOURCE_NOTES.md | entry "2026-10-16 - Batches 15 and 16 finalised", bullet "Cost study, complete per-pair rows" |
| 28 | Cost study, pair 15-16 | 1,145k draft, 393k Fable review, 156k Opus finalisation, 0 new mechanisms | same | same bullet |
| 29 | Cost study, pair 17-18 | 456k Opus draft, 270k Fable review, 145k Opus finalisation, 85k checker work, 1 new mechanism | same | same bullet |
| 30 | Cost study, pair 19-20 | 473k Fable draft, 186k Opus review, 137k Opus finalisation, 12 new mechanisms | same; docs/DECISIONS.md | same bullet; D-46 (b) |
| 31 | Number of decision entries | 59 (D-20260921-01 to D-20261017-59) | docs/DECISIONS.md | headings |

## 4. The lexical floor

| # | Claim | Value | Source file | Where |
|---|---|---|---|---|
| 32 | Audit probe, twin vs malicious, target out | 81.2% accuracy, 0.9 within-family | docs/archive/audit_200_2026-10-16/audit200_report.md | section 3, row "twin vs mal / False / False" |
| 33 | Probe with target or punctuation features | 81.2% (target in), 81.5% (punctuation on), 82.0% (both) | same | section 3, the other three "twin vs mal" rows |
| 34 | Twin vs random, twin vs keyword (target out) | 91.2%, 88.2% | same | section 3, rows "twin vs rand / False / False", "twin vs kw / False / False" |
| 35 | Top separating words | training 19/0, english 18/0, here 15/0; malicious side on_request 0/9, dollars 2/22 | same | section 3, top-features table |
| 36 | Remedy 1, pilot of 40 edits | 81.5% to 81.8%; within-family 90.5% to 90.5%; edited families 40/40 to 39/40 | docs/archive/audit_200_2026-10-16/pilot40_probe.md | "Result" table |
| 37 | Bar for extending the pilot | a fall of five points or more | docs/DECISIONS.md | D-48 (d) |
| 38 | Remedy 2, minimal-pair malicious member | baseline 0.815; A (cue deleted) 0.710, within-family 1.000; C (cue swapped) 0.7925, within-family 0.975 | docs/archive/audit_200_2026-10-16/minpair_probe.md and minpair_probe.json | "Overall" table; JSON "accuracy" fields. The .md prints C as 0.792; D-50 rounds it to 79.3 |
| 39 | Cue share of twin tokens | 0.383 | same .md | "Variant A: share of twin tokens that are cue tokens" |
| 40 | Remedy 3, queries | query only 0.6875 (200), 0.6594 (160 non-query-cue); sentences only 0.8025 (200); full 0.8187 to 0.8125 with queries swapped (160) | docs/archive/audit_200_2026-10-16/query_probe.md | first table |
| 41 | Floor on the evaluation folds | accuracy 79.25 (folds 81.25, 85.0, 77.5, 77.5, 75.0); paired 90.5 (90.0, 95.0, 87.5, 90.0, 90.0); task-type 82.2 / 94.5; operational 77.6 / 88.2 | docs/DATA_CARD.md | "Folds (version 1)", bag-of-words table and the paragraph after it |
| 42 | Topic-mirroring cost estimate | about 1.8M tokens | docs/DECISIONS.md | D-50, alternatives considered |

## 5. Folds and features

| # | Claim | Value | Source file | Where |
|---|---|---|---|---|
| 43 | Fold balance | five families per role per fold; task-type 15, 15, 14, 14, 15 and operational 25, 25, 26, 26, 25; cue positions 7 to 9 per fold | docs/DATA_CARD.md; docs/PROGRESS.md | "Folds (version 1)" table; entry "2026-10-17 - Phase 6: fold assignment ..." |
| 44 | Rounds | 160 training and 40 held-out families (640 and 160 records); leakage zero on every count in all five rounds | docs/PROGRESS.md | same entry, bullet "Leakage" |
| 45 | Family encoder run | 800 records, 6,432 passes, 358 s encoding, 671 s elapsed, 44 files, 116,132,319 bytes | docs/DECISIONS.md | D-54 (a) |

## 6. Fold results (Phase 7)

All rows from `docs/archive/phase7_results_2026-10-17/repo_compatible_tables.md` unless stated.

| # | Claim | Value | Where in the file |
|---|---|---|---|
| 46 | Run | 49 cells, 48 trained, 0 skipped; 48 minutes; 59.3 s mean per trained cell; commit e857b9d7; configuration 65e8db5e1b54 | archive README.md, "Run facts" |
| 47 | BoW row | twin FA 0.190, detection 0.775, paired 0.905 | first table, row "BoW baseline" |
| 48 | N0 row | twin FA 0.515, random FA 0.595, keyword FA 0.460, detection 0.660, paired 0.595 | first table, row "N0 released" |
| 49 | M0 row | 0.542, 0.597, 0.475, 0.677, paired 0.603 | first table, row "M0 base" |
| 50 | M1 row | 0.935, 0.022, 0.058, 0.947, paired 0.547 | first table, row "M1 random" |
| 51 | M2 row | 0.943, 0.040, 0.028, 0.965, paired 0.575 | first table, row "M2 keyword" |
| 52 | M3 row | 0.485, 0.037, 0.013, 0.750, paired 0.842 (± 0.012, f 0.036) | first table, row "M3 semantic" |
| 53 | Spread | seed spread at most 0.042 in any cell of the first table; fold spread 0.018 to 0.084 | first table (D-57 summarises it as "seed spread at most 0.03, fold spread 0.02 to 0.08"; the table wins: M0's random FA has seed spread 0.042 and fold spread 0.084) |
| 54 | Ties | 0 ties in every row | first table, "ties (share)" column |
| 55 | Target-sentence basis | M3 twin FA 0.465, detection 0.750, paired 0.870; M1 0.923 twin FA, M2 0.935; N0 paired 0.530 | section "Held-out families, target sentence basis" |
| 56 | M3 paired by role | analysis 0.920, authorisation 0.907, historical 0.827, negation 0.733, quotation 0.800, task_alignment 0.773, translation 0.880, warning 0.893 | "By semantic role", rows "M3 semantic" |
| 57 | M3 twin FA by role | analysis 0.360, quotation 0.360, historical 0.373, task_alignment 0.467, translation 0.507, authorisation 0.520, negation 0.600, warning 0.693 | same |
| 58 | M3 paired by cue | heading 0.825, policy 0.867, query 0.725, sentence_after 0.908, sentence_before 0.883 | "By cue position", rows "M3 semantic" |
| 59 | M3 twin FA by cue | heading 0.417 to policy 0.542 | same |
| 60 | By attack category | M3 paired operational 0.856, task_type 0.817; BoW 0.882 and 0.945 | "By attack category" |
| 61 | CAD test, N0, minus_near | masked AP 0.995, masked TPR 0.963, all-rows AP 0.871 | "Released CAD test", row n0_released minus_near |
| 62 | CAD test, M0 CPU, minus_near | 0.996, 0.951 | row m0_base minus_near |
| 63 | CAD test, M1 and M2 | masked AP 0.997, masked TPR 1.000 (minus_near) | rows m1_random/all_rounds and m2_keyword/all_rounds minus_near |
| 64 | CAD test, M3 | minus_near masked AP 0.998, masked TPR 0.923; full set masked TPR 0.960 against N0's 0.981 | rows m3_semantic/all_rounds; n0_released full |
| 65 | Four points of upstream recall | 0.963 to 0.923 masked TPR (N0 to M3, minus_near) | rows 61 and 64; wording from D-57 (c) |
| 66 | Float32 ties found by review | 11 tied pairs of 200 when N0 scores the family features with float32 probabilities | docs/DECISIONS.md, D-56 "Context and reason" |

## 7. Retrieval harness (Phase 8)

All rows from `docs/archive/phase8_results_2026-10-17/harness.md` unless stated.

| # | Claim | Value | Where in the file |
|---|---|---|---|
| 67 | Run | exit 0 in 9.05 s on the laptop CPU, commit cfd34d82 | archive README.md, "Run facts" |
| 68 | Store | 216 documents per round: 160 family records, 56 distractor passages from 23 distinct benign remainders (228 sentences) of the 241 leak-excluded test records | archive README.md, "Run facts" |
| 69 | Retrieval | hit@5 0.771, mean rank 11.55; own sentences masked hit@5 0.241, mean rank 46.18; own-match share 0.262 | "Retrieval", row "all" (D-59 (a) gives 0.244, which is round 1's masked value; the "all" row wins, as in the data card) |
| 70 | Slots | malicious 957, twin 1,246, random 653, keyword 797, distractor 347 | "Retrieval", row "all" |
| 71 | Document gate, N0 | pass-through 0.321, twin loss 0.492, family context survival 0.427 | "Document gate", row "N0 released" |
| 72 | Document gate, M1 and M2 | pass-through 0.071 and 0.053; twin loss 0.945 and 0.935 | rows "M1 random", "M2 keyword" |
| 73 | Document gate, M3 | pass-through 0.275, twin loss 0.493, random loss 0.042, keyword loss 0.021, family context survival 0.643 | row "M3 semantic" |
| 74 | Document gate, BoW | pass-through 0.270, twin loss 0.185, family context survival 0.779 (controls and distractors pass unscored) | row "BoW baseline" and the note under the table |
| 75 | Sentence filter, N0 | pass-through 0.600, twin loss 0.392, family context survival 0.789 | "Sentence filter", row "N0 released" |
| 76 | Sentence filter, M0 | 0.567, 0.421, 0.779 | row "M0 base" |
| 77 | Sentence filter, M1 and M2 | pass-through 0.071 and 0.055; twin loss 0.943 and 0.934; survival 0.897 and 0.900 | rows "M1 random", "M2 keyword" |
| 78 | Sentence filter, M3 | pass-through 0.275, twin loss 0.487, family context survival 0.947 | row "M3 semantic" |
| 79 | Distractor loss | 0.049 to 0.073 for every scorer | both gate tables, column "distractor loss" |
| 80 | Role slices, sentence filter | warning twin loss M3 0.757, N0 0.598; negation twin loss M3 0.663; M3 pass-through historical 0.606, quotation 0.417, negation 0.083 | "Sentence filter by semantic role" |
| 81 | Cue slices, sentence filter | M3 pass-through heading 0.360, sentence_before 0.342, sentence_after 0.191 (twin loss there 0.574); M1 and M2 heading twin loss 0.991 and 0.989 | "Sentence filter by cue position" |
| 82 | Derived phrases in the adopted reading | "two thirds" stopped (N0 document gate, 1 - 0.321); "93 to 95 percent" stopped (M1, M2); "72 percent" stopped (M3); "95 percent" of context kept (M3 sentence filter) | docs/DECISIONS.md, D-59 (c), from rows 71 to 78 |

## 8. Compute and engineering

| # | Claim | Value | Source file | Where |
|---|---|---|---|---|
| 83 | Budget pools | A 6 h / 12 units; B 4 h / 8 units; C 6 h / 12 units; D 8 h / 16 units; total 24 h / 48 units | docs/DECISIONS.md | D-17 |
| 84 | Pool use | A 2,369 s / 0.6 units; B 1 h 12 min / 2.17 units; C 671 s / about 0.3 units; D unused | docs/DECISIONS.md; docs/PROGRESS.md | D-53 (d); m0 entry of 2026-10-04; D-54 (c); Phases 7 and 8 ran on CPU (archive READMEs) |
| 85 | Use before the pools | 7,200 s and 1.84 units | docs/DECISIONS.md | D-17 |
| 86 | Gate reproducibility | three gate passes on three code versions gave the same fingerprint and the same reference probabilities (3.0e-11, 0.437, 7.0e-08) | Project\REPORT_SOURCE_NOTES.md | section 4, "Third gate pass and profile re-freeze" |
| 87 | Tests | 367 passed at the Phase 8 build | docs/PROGRESS.md | entry "2026-10-17 - Phase 8: retrieval harness built", bullet "Tests" |

## 9. Facts from the papers (verify before use)

| # | Claim | Value | Source | Note |
|---|---|---|---|---|
| 88 | CAD ablation on AgentDyn | removing the query: clean utility 36.7% to 28.3%, static attack success 3.5% to 7.9%; removing the context: clean utility 16.7% | the literature review, Section II-C | as the team wrote it; check against [6] |
| 89 | CAD main table, GPT-4o-mini, AgentDojo | no defence CU 65.8 / UA 43.3 / ASR 59.6; PIGuard 44.5 / 31.7 / 0.0; CAD full 57.6 / 50.6 / 0.0; CAD without context 60.8 / 52.0 / 0.3 | Project\REPORT_SOURCE_NOTES.md section 1.1 | read from the arXiv HTML v1; the notes say to re-verify against the PDF |
| 90 | CAD training data | 24,665 sentence rows from three LLM calls per example; injection at a random sentence boundary | Project\REPORT_SOURCE_NOTES.md section 1.0 | verify against [6] |

## 10. Conflicts found between sources, and the value to use

| Topic | Values found | Use | Why |
|---|---|---|---|
| Masked hit@5 | 0.244 (D-59 (a), REPORT_SOURCE_NOTES) vs 0.241 (harness.md "all", DATA_CARD, PROGRESS) | 0.241 | 0.244 is round 1 only |
| Remedy 2 bound C | 0.792 (minpair_probe.md), 0.7925 (JSON), 79.3 (D-50) | 79.25% | the JSON is the exact value |
| BoW accuracy | 81.2 (audit), 81.5 (after reopening), 79.25 (folds_v1) | 79.25 beside the fold results; 81.5 when describing the floor of the data set | different folds and data states; say which |
| Seed and fold spread | D-57 "seed at most 0.03, fold 0.02 to 0.08" vs table max 0.042 and 0.084 | the table | the table is the measurement |
| Meaning of N0 | "no scorer" in the early plan (REPORT_SOURCE_NOTES section 3) vs the released checkpoint (D-55) | the released checkpoint; the no-scorer reference is the "no gate" row | D-55 is the decision used by every result table |
| Deadline | 26 October (handout; D-58) vs 25 October 23:59 (Canvas page) | 25 October | the earlier date is safe |
| PDF locations | the brief named `COMPSCI764\` for the handout and the literature review | both are in `C:\Users\songh\Downloads\` | found there |

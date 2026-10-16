# 200-family audit: measurements (D-20261016-46 d)

Repository at phase5-batch-20 2b598dc; 800 records, 200 families. Measurement only; no repository file changed.

## 1. Full-set checks

prescreen over all_800.jsonl (manifest as --families): exit 0; 200 families passed, 0 failed, role counts 25 each, cue positions 40 each, 200 'awaiting_review' family warnings (manifest status candidate).

validate over all_800.jsonl: exit 0; 800 records, 2816 sentence rows, 0 exact duplicate records, 0 cross-group exact or near (0.8) duplicates, 0 families with differing targets.

Self-check per batch (current checker, --previous every earlier batch, prompt v3, semantic answers). Exit codes for --stage drafting and --stage review. Counts are detail items per FAIL/WARN check.

| batch | exit drafting | exit review | overall now | overall at finalisation | FAIL checks | WARN checks | check: status items |
|---|---|---|---|---|---|---|---|
| 01 | 2 | 2 | FAIL | WARN | 1 | 6 | M6_lexical_skew WARN 5; M9_queries WARN 3; M12_manifest_provenance FAIL 40; M14_coverage WARN 2; M16_hard_negative WARN 1; M17_residual_cue_markers WARN 6; S_semantic_answers WARN 19 |
| 02 | 2 | 2 | FAIL | WARN | 1 | 6 | M6_lexical_skew WARN 3; M9_queries WARN 3; M12_manifest_provenance FAIL 40; M14_coverage WARN 6; M16_hard_negative WARN 1; M17_residual_cue_markers WARN 8; S_semantic_answers WARN 20 |
| 03 | 2 | 2 | FAIL | WARN | 1 | 5 | M6_lexical_skew WARN 5; M9_queries WARN 2; M12_manifest_provenance FAIL 40; M14_coverage WARN 10; M17_residual_cue_markers WARN 4; S_semantic_answers WARN 8 |
| 04 | 2 | 2 | FAIL | PASS | 1 | 5 | M6_lexical_skew WARN 2; M9_queries WARN 2; M12_manifest_provenance FAIL 40; M14_coverage WARN 8; M17_residual_cue_markers WARN 8; S_semantic_answers WARN 8 |
| 05 | 2 | 2 | FAIL | WARN | 2 | 5 | M6_lexical_skew WARN 1; M9_queries WARN 3; M12_manifest_provenance FAIL 40; M14_coverage WARN 10; M17_residual_cue_markers WARN 7; M19_batch_confound WARN 2; S_semantic_answers FAIL 19 |
| 06 | 0 | 0 | WARN | WARN | 0 | 5 | M6_lexical_skew WARN 2; M9_queries WARN 2; M14_coverage WARN 3; M17_residual_cue_markers WARN 13; S_semantic_answers WARN 20 |
| 07 | 0 | 0 | WARN | WARN | 0 | 5 | M6_lexical_skew WARN 2; M9_queries WARN 1; M14_coverage WARN 2; M17_residual_cue_markers WARN 12; S_semantic_answers WARN 21 |
| 08 | 0 | 0 | WARN | WARN | 0 | 4 | M9_queries WARN 1; M14_coverage WARN 2; M17_residual_cue_markers WARN 12; S_semantic_answers WARN 22 |
| 09 | 0 | 0 | WARN | WARN | 0 | 5 | M9_queries WARN 1; M14_coverage WARN 3; M17_residual_cue_markers WARN 14; M18_weak_cue_marker WARN 1; S_semantic_answers WARN 11 |
| 10 | 0 | 0 | WARN | WARN | 0 | 5 | M9_queries WARN 1; M14_coverage WARN 2; M17_residual_cue_markers WARN 7; M18_weak_cue_marker WARN 1; S_semantic_answers WARN 11 |
| 11 | 0 | 0 | WARN | WARN | 0 | 3 | M9_queries WARN 1; M14_coverage WARN 2; S_semantic_answers WARN 1 |
| 12 | 0 | 0 | WARN | WARN | 0 | 3 | M9_queries WARN 1; M14_coverage WARN 4; M18_weak_cue_marker WARN 1 |
| 13 | 0 | 0 | WARN | WARN | 0 | 1 | M9_queries WARN 1 |
| 14 | 0 | 0 | WARN | WARN | 0 | 2 | M9_queries WARN 1; M14_coverage WARN 1 |
| 15 | 0 | 0 | WARN | WARN | 0 | 4 | M9_queries WARN 1; M14_coverage WARN 1; M18_weak_cue_marker WARN 1; M19_batch_confound WARN 1 |
| 16 | 0 | 0 | WARN | WARN | 0 | 3 | M9_queries WARN 1; M14_coverage WARN 3; M19_batch_confound WARN 1 |
| 17 | 0 | 0 | WARN | WARN | 0 | 3 | M9_queries WARN 1; M14_coverage WARN 3; M19_batch_confound WARN 1 |
| 18 | 0 | 0 | WARN | WARN | 0 | 3 | M9_queries WARN 1; M14_coverage WARN 4; M19_batch_confound WARN 1 |
| 19 | 0 | 0 | WARN | WARN | 0 | 3 | M9_queries WARN 1; M14_coverage WARN 6; M19_batch_confound WARN 1 |
| 20 | 0 | 0 | WARN | WARN | 0 | 4 | M9_queries WARN 1; M14_coverage WARN 9; M18_weak_cue_marker WARN 1; M19_batch_confound WARN 1 |

Retroactive view (items in a FAIL/WARN check now that are absent from the batch's finalised report in review/): 532 items (219 under FAIL checks, 313 under WARN checks). M12 accounts for 200. Full list in retroactive.json.

| batch | check | status now | status at finalisation | new items |
|---|---|---|---|---|
| 01 | M12_manifest_provenance | FAIL | PASS | 40 |
| 01 | M14_coverage | WARN | PASS | 2 |
| 01 | M16_hard_negative | WARN | WARN | 1 |
| 01 | M17_residual_cue_markers | WARN | PASS | 6 |
| 01 | M6_lexical_skew | WARN | WARN | 1 |
| 01 | M9_queries | WARN | WARN | 2 |
| 01 | S_semantic_answers | WARN | PASS | 19 |
| 02 | M12_manifest_provenance | FAIL | PASS | 40 |
| 02 | M14_coverage | WARN | PASS | 6 |
| 02 | M16_hard_negative | WARN | WARN | 1 |
| 02 | M17_residual_cue_markers | WARN | PASS | 8 |
| 02 | M6_lexical_skew | WARN | WARN | 1 |
| 02 | M9_queries | WARN | WARN | 2 |
| 02 | S_semantic_answers | WARN | PASS | 20 |
| 03 | M12_manifest_provenance | FAIL | PASS | 40 |
| 03 | M14_coverage | WARN | PASS | 10 |
| 03 | M17_residual_cue_markers | WARN | PASS | 4 |
| 03 | M6_lexical_skew | WARN | WARN | 3 |
| 03 | M9_queries | WARN | PASS | 2 |
| 03 | S_semantic_answers | WARN | PASS | 8 |
| 04 | M12_manifest_provenance | FAIL | PASS | 40 |
| 04 | M14_coverage | WARN | PASS | 8 |
| 04 | M17_residual_cue_markers | WARN | PASS | 8 |
| 04 | M6_lexical_skew | WARN | PASS | 2 |
| 04 | M9_queries | WARN | PASS | 2 |
| 04 | S_semantic_answers | WARN | PASS | 8 |
| 05 | M12_manifest_provenance | FAIL | PASS | 40 |
| 05 | M14_coverage | WARN | PASS | 10 |
| 05 | M17_residual_cue_markers | WARN | PASS | 7 |
| 05 | M19_batch_confound | WARN | WARN | 1 |
| 05 | M6_lexical_skew | WARN | PASS | 1 |
| 05 | M9_queries | WARN | PASS | 3 |
| 05 | S_semantic_answers | FAIL | PASS | 19 |
| 06 | M14_coverage | WARN | PASS | 3 |
| 06 | M17_residual_cue_markers | WARN | PASS | 13 |
| 06 | M6_lexical_skew | WARN | PASS | 2 |
| 06 | M9_queries | WARN | PASS | 2 |
| 06 | S_semantic_answers | WARN | PASS | 20 |
| 07 | M14_coverage | WARN | PASS | 2 |
| 07 | M17_residual_cue_markers | WARN | PASS | 12 |
| 07 | M6_lexical_skew | WARN | PASS | 2 |
| 07 | S_semantic_answers | WARN | PASS | 21 |
| 08 | M14_coverage | WARN | PASS | 2 |
| 08 | M17_residual_cue_markers | WARN | PASS | 12 |
| 08 | S_semantic_answers | WARN | PASS | 22 |
| 09 | M14_coverage | WARN | PASS | 3 |
| 09 | M17_residual_cue_markers | WARN | PASS | 14 |
| 09 | S_semantic_answers | WARN | PASS | 11 |
| 10 | M14_coverage | WARN | PASS | 2 |
| 10 | M17_residual_cue_markers | WARN | PASS | 7 |
| 10 | S_semantic_answers | WARN | PASS | 11 |
| 11 | M14_coverage | WARN | WARN | 1 |
| 11 | S_semantic_answers | WARN | PASS | 1 |
| 12 | M14_coverage | WARN | WARN | 3 |
| 16 | M14_coverage | WARN | WARN | 1 |

M12 example items: {"family_id": "pilot_0001", "record": "shared_malicious", "problem": "generator_prompt_hash does not match the prompt file"}; {"family_id": "pilot_0001", "record": "semantic_benign", "problem": "generator_prompt_hash does not match the prompt file"}; {"family_id": "pilot_0001", "record": "random_benign", "problem": "generator_prompt_hash does not match the prompt file"}

M12 check: batches 01 to 05 carry the DRAFTING_PROMPT_v2 hash (30d7b72f), batches 06 to 20 the v3 hash (09d56ad2). Rerun of 01 to 05 with --prompt v2: exits 01:0, 02:0, 03:0, 04:0, 05:2; M12 then passes, so the 200 M12 items are a prompt-version artefact of the v3 rerun. Batch 05 still FAILs S_semantic_answers: ten S13 answers are missing (pilot_0041 to pilot_0050; S13 was required after batch 05 was finalised).

Retroactive items other than M12 (332), grouped by check and problem (per-item list in retroactive.json):

| check | status | problem | items | batches |
|---|---|---|---|---|
| S_semantic_answers | WARN | S1 does not quote the twin query with the label [asks] or [asserts] (D-20261015-34; WARN) | 54 | 01,02,03,04,06,07,08 |
| S_semantic_answers | WARN | S13 answers for the malicious document only; name the twin's document type and say why the request is foreign there too (D-20261015-36; WARN) | 50 | 06,07,08,09,10 |
| M17_residual_cue_markers | WARN | a context sentence echoes the tagged cue's distinctive words: a second carrier of the benign reading (R6, D-20261015-36; S1 decides) | 46 | 01,02,03,04,05,06,07,08,09,10 |
| M17_residual_cue_markers | WARN | the twin query echoes the tagged cue's distinctive words: a second carrier of the benign reading (R6, D-20261014-33, D-20261015-36) | 33 | 01,02,03,04,05,06,07,08,09,10 |
| S_semantic_answers | WARN | S12 compares only with this batch or the previous one; name the closest earlier twin of the role from the whole cue index (D-20261016-42; WARN) | 30 | 01,02,06,07,08,09,10,11 |
| M14_coverage | WARN | cue sentences of the same role share a masked skeleton: the frame repeats with other nouns (R15, D-20261014-31; S12 names the frame) | 14 | 02,03,04,05,06,07 |
| M17_residual_cue_markers | WARN | the twin opens as a request-hosting genre, which carries the benign reading without the cue (D-20261015-34 venue rule, D-20261015-36; S13 decides) | 10 | 01,04,06,07,08,09,10 |
| S_semantic_answers | FAIL | S13 answer missing (required YES) | 10 | 05 |
| M6_lexical_skew | WARN | watch token present in two or more twins and no malicious member (D-20261014-30) | 9 | 01,02,03,04,05,06,07 |
| M14_coverage | WARN | cue sentences of the same role and cue position overlap in content words (R15/R25, D-20261014-30; S12 names the frame) | 8 | 03,04,05 |
| S_semantic_answers | FAIL | S1 does not quote the twin query with the label [asks] or [asserts] (D-20261015-34; WARN) | 8 | 05 |
| M9_queries | WARN | query token or bigram skewed to one pair side across the set (D-20261014-30; gap form D-20261014-31) | 6 | 01,02,03,04,05,06 |
| M9_queries | WARN | queries near-reused across the set: most content tokens shared, or the same opening on one pair side (R14, D-20261014-31) | 6 | 01,02,03,04,05,06 |
| M14_coverage | WARN | cue device not named in the manifest justification ('device: <slug>', D-20261014-31) | 6 | 01,02,03,04,05,06 |
| S_semantic_answers | WARN | S11 does not restate the manifest justification (a stale answer or a stale justification; D-20261014-33; WARN) | 6 | 01,02,07 |
| M14_coverage | WARN | cue mechanism genus not named in the manifest justification ('mechanism: <genus>', D-20261015-41) | 6 | 07,08,09,10,11,12 |
| M14_coverage | WARN | pair queries of the batch open with the same two words (R14, D-20261015-34) | 5 | 01,02,03,04,05 |
| M14_coverage | WARN | cue sentences of the same role overlap in content words whatever the cue position (R15, D-20261014-33; S12 names the frame) | 4 | 03,04,05 |
| M14_coverage | WARN | two or more twins of the batch carry an exemplar word in the cue, the frame S12 cannot see across roles (R15, D-20261015-34) | 3 | 03,06,08 |
| M6_lexical_skew | WARN | watch token present in two or more malicious members and no twin (D-20261014-33) | 3 | 04,06,07 |
| M16_hard_negative | WARN | no malicious member in a security/moderation-themed document | 2 | 01,02 |
| M14_coverage | WARN | one cue device covers more than half of a role's tagged twins (R15, D-20261014-31) | 2 | 09,10 |
| M17_residual_cue_markers | WARN | cue-marker words in the twin query although the cue is elsewhere (R6) | 1 | 01 |
| S_semantic_answers | WARN | S4 is not YES although cue_position is query: the malicious query does not make the twin an injection, so the query is not the only cue (R6, D-2026101 | 1 | 02 |
| M14_coverage | WARN | policy cue of pilot_0026 opens with the same 2 tokens 'under the' as the policy cue of earlier family pilot_0011, across roles (literal opener test, R | 1 | 03 |
| M9_queries | WARN | question-form share differs across pair sides (D-20261014-30) | 1 | 05 |
| M19_batch_confound | WARN | share of targets phrased 'your response/reply/answer' differs sharply from the last two batches | 1 | 05 |
| S_semantic_answers | FAIL | S11 does not restate the manifest justification (a stale answer or a stale justification; D-20261014-33; WARN) | 1 | 05 |
| M17_residual_cue_markers | WARN | identifier echo in pilot_0063: the target's digit string 829374 recurs in the twin sentence 0, a lexical bridge between target and cue (D-20261016-44  | 1 | 07 |
| M14_coverage | WARN | policy cue of pilot_0084 opens with the same 2 tokens 'under the' as the policy cue of earlier family pilot_0011, across roles (literal opener test, R | 1 | 09 |
| M14_coverage | WARN | policy cue of pilot_0116 opens with the same 2 tokens 'under the' as the policy cue of earlier family pilot_0011, across roles (literal opener test, R | 1 | 12 |
| M14_coverage | WARN | policy cue of pilot_0118 opens with the same 2 tokens 'under the' as the policy cue of earlier family pilot_0011, across roles (literal opener test, R | 1 | 12 |
| M14_coverage | WARN | policy cue of pilot_0152 opens with the same 2 tokens 'under the' as the policy cue of earlier family pilot_0011, across roles (literal opener test, R | 1 | 16 |

## 2. Lexical tells by record kind

(a) Non-target sentences ending in a colon.

| kind | records with >=1 | sentences | queries ending ':' | records with any ':' in non-target |
|---|---|---|---|---|
| mal | 0/200 (0.0%) | 0/504 (0.0%) | 0 | 7 |
| twin | 16/200 (8.0%) | 16/504 (3.2%) | 0 | 59 |
| rand | 0/200 (0.0%) | 0/704 (0.0%) | 0 | 2 |
| kw | 0/200 (0.0%) | 0/704 (0.0%) | 0 | 5 |

Twin cue sentences (located with selfcheck._cue_sentence_ids; the 40 query-position twins have none): 16 of 160 have one ending in a colon; by cue position {'sentence_before': 12, 'heading': 2, 'policy': 2}; by role {'analysis': 6, 'historical_description': 2, 'authorisation': 1, 'quotation': 4, 'warning': 1, 'translation': 2}; by batch {14: 2, 15: 2, 17: 2, 18: 5, 19: 3, 20: 2}. Twins with a colon-ended non-target sentence outside the located cue: 0 ().

(b) Non-target sentences opening with each word (count, share of non-target sentences).

| kind | That | Under the | After | This | Please | n sentences |
|---|---|---|---|---|---|---|
| mal | 0 (0.0%) | 0 (0.0%) | 2 (0.4%) | 0 (0.0%) | 2 (0.4%) | 504 |
| twin | 16 (3.2%) | 6 (1.2%) | 0 (0.0%) | 7 (1.4%) | 0 (0.0%) | 504 |
| rand | 0 (0.0%) | 0 (0.0%) | 2 (0.3%) | 0 (0.0%) | 1 (0.1%) | 704 |
| kw | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 1 (0.1%) | 0 (0.0%) | 704 |
| twin cue sentences | 16 (10.0%) | 6 (3.8%) | 0 (0.0%) | 2 (1.2%) | 0 (0.0%) | 160 |

Twin cue sentences opening with That: 16 families; overlap with the colon-ended cues: 0; twins carrying either tell: 32 of 200. That-cue families by batch {1: 1, 3: 1, 4: 1, 5: 1, 11: 2, 13: 1, 14: 1, 15: 2, 16: 2, 19: 2, 20: 2}; by cue position {'sentence_after': 14, 'policy': 2}; by role {'negation': 3, 'quotation': 4, 'historical_description': 2, 'warning': 2, 'translation': 2, 'authorisation': 3}.

Records with at least one such sentence (of 200): mal That 0, Under the 0, After 2, This 0, Please 2; twin That 16, Under the 6, After 0, This 7, Please 0; rand That 0, Under the 0, After 2, This 0, Please 1; kw That 0, Under the 0, After 0, This 1, Please 0

(c) Query openers. Top first words by kind: mal: summarise 37, what 33, how 29, which 29, list 13, draft 12; twin: summarise 35, what 27, which 18, when 15, how 14, does 10; rand: how 52, when 35, where 21, what 19, summarise 17, explain 16; kw: what 57, summarise 49, how 19, which 19, describe 12, set 11

Top first two words: mal: summarise the 27, list the 13, what does 13, draft a 10, summarise this 8; twin: summarise the 20, summarise this 14, what does 8, does the 8, write the 6; rand: how do 22, summarise the 17, when does 15, explain how 13, how does 12; kw: summarise the 49, what does 32, what did 18, set out 11, how does 6

Openers whose share differs by more than ten points between twin and malicious (counts of 200):

| words | opener | mal | twin | rand | kw | twin-mal pts |
|---|---|---|---|---|---|---|
| - | none |  |  |  |  |  |

(d) Length (characters over sentences; query separately).

| kind | mean chars | median chars | mean sentences | median sentences | mean query chars |
|---|---|---|---|---|---|
| mal | 425 | 413.0 | 3.52 | 4.0 | 61.5 |
| twin | 426.1 | 418.5 | 3.52 | 4.0 | 69.5 |
| rand | 393.7 | 383.0 | 3.52 | 4.0 | 52.1 |
| kw | 400.9 | 390.0 | 3.52 | 4.0 | 58.5 |

Twin longer than malicious: 105/200 (52.5%); twin minus malicious characters mean 1.1, median 1.0. Per batch (of 10): 01:3, 02:6, 03:5, 04:5, 05:6, 06:6, 07:5, 08:5, 09:5, 10:6, 11:5, 12:5, 13:5, 14:4, 15:7, 16:5, 17:5, 18:7, 19:5, 20:5

(e) Log-odds twin vs mal (add-one, words in >=10 records; non-target sentences plus query). word log-odds (count A/count B).

| # | favours twin | favours malicious |
|---|---|---|
| 1 | training 2.98 (19/0) | dollars -2.05 (2/22) |
| 2 | english 2.93 (18/0) | need -2.03 (1/14) |
| 3 | here 2.76 (15/0) | thirty -1.89 (1/12) |
| 4 | written 2.38 (10/0) | twelve -1.89 (1/12) |
| 5 | editor 2.0 (14/1) | collect -1.72 (1/10) |
| 6 | pages 1.83 (18/2) | receipt -1.69 (2/15) |
| 7 | went 1.78 (11/1) | if -1.48 (2/12) |
| 8 | vendor 1.72 (16/2) | should -1.48 (2/12) |
| 9 | guide 1.69 (21/3) | free -1.34 (3/14) |
| 10 | copied 1.59 (9/1) | rate -1.3 (4/17) |
| 11 | text 1.59 (19/3) | cost -1.22 (2/9) |
| 12 | quarter 1.59 (19/3) | leaves -1.22 (2/9) |
| 13 | june 1.52 (13/2) | car -1.21 (6/22) |
| 14 | came 1.52 (13/2) | key -1.19 (3/12) |
| 15 | version 1.45 (12/2) | bring -1.19 (3/12) |
| 16 | policy 1.41 (24/5) | fee -1.11 (7/23) |
| 17 | you 1.37 (11/2) | wednesday -1.11 (3/11) |
| 18 | did 1.37 (11/2) | order -1.07 (6/19) |
| 19 | message 1.33 (22/5) | collected -1.03 (3/10) |
| 20 | case 1.31 (14/3) | get -1.03 (3/10) |

(e) Log-odds twin vs controls (add-one, words in >=10 records; non-target sentences plus query). word log-odds (count A/count B).

| # | favours twin | favours controls |
|---|---|---|
| 1 | here 3.45 (15/0) | academic -2.21 (0/17) |
| 2 | words 3.24 (12/0) | large -2.15 (0/16) |
| 3 | editor 2.69 (14/1) | lock -2.03 (0/14) |
| 4 | policy 2.51 (24/3) | deposit -2.03 (0/14) |
| 5 | job 2.47 (11/1) | available -2.03 (0/14) |
| 6 | language 2.29 (14/2) | access -2.03 (1/29) |
| 7 | copied 2.29 (9/1) | planned -1.96 (0/13) |
| 8 | english 2.24 (18/3) | limit -1.96 (0/13) |
| 9 | text 2.07 (19/4) | visitors -1.96 (0/13) |
| 10 | pages 2.01 (18/4) | explain -1.89 (1/25) |
| 11 | sheet 1.98 (32/8) | but -1.81 (0/11) |
| 12 | draft 1.86 (12/3) | stored -1.81 (0/11) |
| 13 | this 1.74 (126/43) | describe -1.76 (1/22) |
| 14 | put 1.69 (10/3) | twelve -1.76 (1/22) |
| 15 | reply 1.66 (23/8) | if -1.66 (2/30) |
| 16 | version 1.63 (12/4) | ward -1.62 (1/19) |
| 17 | me 1.63 (12/4) | instead -1.62 (1/19) |
| 18 | letter 1.6 (14/5) | explains -1.62 (5/59) |
| 19 | guide 1.57 (21/8) | reports -1.59 (2/28) |
| 20 | carried 1.55 (11/4) | changed -1.57 (1/18) |

(f) Digit strings (>=4 digits) of the family's target echoed in the record's query or non-target sentences (85 targets carry such a string; controls compared with the family target).

| kind | records | families |
|---|---|---|
| mal | 0 |  |
| twin | 1 | 0063 |
| rand | 0 |  |
| kw | 2 | 0104, 0126 |

(g) Records whose query or non-target sentences contain each word (selfcheck.WATCH_TOKENS, POLICY_WORDS, POLICY_LEXICON).

| word | mal | twin | rand | kw |
|---|---|---|---|---|
| instruction | 3 | 9 | 0 | 0 |
| instructions | 3 | 2 | 0 | 1 |
| directive | 0 | 0 | 0 | 0 |
| directives | 0 | 0 | 0 | 0 |
| entry | 3 | 10 | 1 | 4 |
| entries | 1 | 4 | 3 | 1 |
| follow | 3 | 2 | 1 | 2 |
| follows | 0 | 7 | 2 | 2 |
| words | 3 | 12 | 0 | 0 |
| note | 18 | 26 | 8 | 9 |
| notes | 4 | 11 | 6 | 10 |
| notice | 21 | 11 | 14 | 10 |
| notices | 0 | 4 | 1 | 1 |
| records | 6 | 14 | 1 | 25 |
| log | 6 | 10 | 0 | 6 |
| logs | 0 | 0 | 0 | 3 |
| digest | 5 | 8 | 1 | 2 |
| policy | 4 | 24 | 3 | 0 |
| policies | 0 | 0 | 0 | 0 |
| rule | 3 | 2 | 0 | 1 |
| rules | 6 | 16 | 4 | 5 |
| handbook | 2 | 8 | 2 | 0 |
| practice | 6 | 15 | 8 | 12 |
| authorisation | 0 | 1 | 0 | 1 |
| authorization | 0 | 0 | 0 | 1 |
| permission | 0 | 0 | 0 | 2 |
| permits | 0 | 2 | 3 | 0 |

## 3. Shortcut probe

scikit-learn is not importable in the repository interpreter (ModuleNotFoundError), so the probe is a multinomial naive Bayes written here (Laplace alpha 1, unigrams plus bigrams over selfcheck.normalise tokens, which drop punctuation), five folds grouped by family_id (families shuffled with seed 764; each family's records in one fold). A second variant adds punctuation tokens, a colon-ended-sentence token and the first word of each sentence and of the query. Classes are balanced (200 each); chance is 50%.

| A vs B | target included | punctuation/opener features | accuracy | balanced acc | paired acc (A scored above B within family) | fold acc |
|---|---|---|---|---|---|---|
| twin vs mal | False | False | 0.812 | 0.812 | 0.9 | [0.838, 0.825, 0.787, 0.838, 0.775] |
| twin vs mal | False | True | 0.815 | 0.815 | 0.905 | [0.838, 0.825, 0.787, 0.825, 0.8] |
| twin vs mal | True | False | 0.812 | 0.812 | 0.905 | [0.825, 0.85, 0.787, 0.812, 0.787] |
| twin vs mal | True | True | 0.82 | 0.82 | 0.915 | [0.85, 0.85, 0.787, 0.825, 0.787] |
| twin vs rand | False | False | 0.912 | 0.912 | 0.98 | [0.912, 0.912, 0.938, 0.925, 0.875] |
| twin vs rand | False | True | 0.92 | 0.92 | 0.98 | [0.925, 0.9, 0.95, 0.938, 0.887] |
| twin vs rand | True | False | 0.965 | 0.965 | 0.99 | [0.95, 0.988, 0.963, 0.963, 0.963] |
| twin vs rand | True | True | 0.975 | 0.975 | 0.99 | [0.975, 0.988, 0.963, 0.975, 0.975] |
| twin vs kw | False | False | 0.882 | 0.883 | 0.97 | [0.938, 0.912, 0.825, 0.863, 0.875] |
| twin vs kw | False | True | 0.897 | 0.897 | 0.98 | [0.95, 0.912, 0.875, 0.85, 0.9] |
| twin vs kw | True | False | 0.927 | 0.927 | 0.99 | [0.963, 0.963, 0.85, 0.9, 0.963] |
| twin vs kw | True | True | 0.95 | 0.95 | 0.99 | [0.963, 0.988, 0.912, 0.925, 0.963] |

Top features (min 5 records), twin vs mal, target out, punctuation features off (feature count A/count B).

| # | favours twin | favours mal |
|---|---|---|
| 1 | training (19/0) | on_request (0/9) |
| 2 | english (18/0) | network (0/8) |
| 3 | here (15/0) | valid (0/8) |
| 4 | of_its (12/0) | visitor (1/16) |
| 5 | written (10/0) | transfers (0/7) |
| 6 | handover (9/0) | visitors (0/7) |
| 7 | the_training (9/0) | page_asks (0/7) |
| 8 | centre_s (9/0) | note_on (0/7) |
| 9 | act_on (8/0) | the_building (0/7) |
| 10 | logged (8/0) | long_does (0/7) |
| 11 | her (8/0) | dollars (2/22) |
| 12 | act (8/0) | need (1/14) |
| 13 | passage (8/0) | the_original (0/6) |
| 14 | our (8/0) | of_purchase (0/6) |
| 15 | task (8/0) | thirty_days (0/6) |
| 16 | that_request (7/0) | the_key (0/6) |
| 17 | week_with (7/0) | original (0/6) |
| 18 | brief (7/0) | are_collected (0/6) |
| 19 | exactly (7/0) | thirty (1/12) |
| 20 | follows (7/0) | twelve (1/12) |

Top features (min 5 records), twin vs mal, target out, punctuation features on (feature count A/count B).

| # | favours twin | favours mal |
|---|---|---|
| 1 | training (19/0) | on_request (0/9) |
| 2 | english (18/0) | S:FIRST_two (0/9) |
| 3 | S:FIRST_that (16/0) | network (0/8) |
| 4 | P:END_COLON (16/0) | valid (0/8) |
| 5 | here (15/0) | visitor (1/16) |
| 6 | of_its (12/0) | transfers (0/7) |
| 7 | written (10/0) | visitors (0/7) |
| 8 | handover (9/0) | page_asks (0/7) |
| 9 | the_training (9/0) | note_on (0/7) |
| 10 | centre_s (9/0) | the_building (0/7) |
| 11 | act_on (8/0) | long_does (0/7) |
| 12 | logged (8/0) | dollars (2/22) |
| 13 | her (8/0) | need (1/14) |
| 14 | act (8/0) | the_original (0/6) |
| 15 | passage (8/0) | of_purchase (0/6) |
| 16 | our (8/0) | thirty_days (0/6) |
| 17 | task (8/0) | the_key (0/6) |
| 18 | S:FIRST_under (8/0) | original (0/6) |
| 19 | P:: (65/7) | are_collected (0/6) |
| 20 | that_request (7/0) | thirty (1/12) |

Top features (min 5 records), twin vs mal, target in, punctuation features off (feature count A/count B).

| # | favours twin | favours mal |
|---|---|---|
| 1 | here (15/0) | on_request (0/9) |
| 2 | of_its (12/0) | visitor (1/16) |
| 3 | written (10/0) | transfers (0/7) |
| 4 | training (20/1) | visitors (0/7) |
| 5 | english (19/1) | page_asks (0/7) |
| 6 | handover (9/0) | note_on (0/7) |
| 7 | the_training (9/0) | the_building (0/7) |
| 8 | centre_s (9/0) | long_does (0/7) |
| 9 | act_on (8/0) | dollars (2/22) |
| 10 | logged (8/0) | need (1/14) |
| 11 | her (8/0) | the_original (0/6) |
| 12 | act (8/0) | of_purchase (0/6) |
| 13 | passage (8/0) | thirty_days (0/6) |
| 14 | task (8/0) | original (0/6) |
| 15 | that_request (7/0) | are_collected (0/6) |
| 16 | week_with (7/0) | thirty (1/12) |
| 17 | brief (7/0) | twelve (1/12) |
| 18 | exactly (7/0) | price (1/12) |
| 19 | follows (7/0) | nurse (0/5) |
| 20 | the_clerk (7/0) | week_before (0/5) |

Top features (min 5 records), twin vs mal, target in, punctuation features on (feature count A/count B).

| # | favours twin | favours mal |
|---|---|---|
| 1 | S:FIRST_that (16/0) | on_request (0/9) |
| 2 | P:END_COLON (16/0) | S:FIRST_two (0/9) |
| 3 | here (15/0) | visitor (1/16) |
| 4 | of_its (12/0) | transfers (0/7) |
| 5 | written (10/0) | visitors (0/7) |
| 6 | training (20/1) | page_asks (0/7) |
| 7 | english (19/1) | note_on (0/7) |
| 8 | handover (9/0) | the_building (0/7) |
| 9 | the_training (9/0) | long_does (0/7) |
| 10 | centre_s (9/0) | dollars (2/22) |
| 11 | act_on (8/0) | need (1/14) |
| 12 | logged (8/0) | the_original (0/6) |
| 13 | her (8/0) | of_purchase (0/6) |
| 14 | act (8/0) | thirty_days (0/6) |
| 15 | passage (8/0) | original (0/6) |
| 16 | task (8/0) | are_collected (0/6) |
| 17 | S:FIRST_under (8/0) | thirty (1/12) |
| 18 | that_request (7/0) | twelve (1/12) |
| 19 | week_with (7/0) | price (1/12) |
| 20 | brief (7/0) | nurse (0/5) |

Top features (min 5 records), twin vs rand, target out, punctuation features off (feature count A/count B).

| # | favours twin | favours rand |
|---|---|---|
| 1 | pages (18/0) | do_i (0/19) |
| 2 | english (18/0) | visitors (0/13) |
| 3 | the_records (18/0) | explain_how (0/13) |
| 4 | vendor (16/0) | lock (0/13) |
| 5 | here (15/0) | deposit (0/13) |
| 6 | log (15/0) | large (0/11) |
| 7 | editor (14/0) | go_in (0/10) |
| 8 | summarise_this (14/0) | replacement (0/9) |
| 9 | this (126/8) | saturdays (0/9) |
| 10 | bulletin (13/0) | locks (0/8) |
| 11 | in_this (13/0) | hospital (0/8) |
| 12 | question (13/0) | limit (0/8) |
| 13 | of_this (13/0) | on_request (0/8) |
| 14 | words (12/0) | for_three (0/8) |
| 15 | the_vendor (12/0) | page_asks (0/8) |
| 16 | of_its (12/0) | to_use (0/8) |
| 17 | draft (12/0) | if_the (0/8) |
| 18 | records (24/1) | available (0/8) |
| 19 | reply (23/1) | is_out (0/8) |
| 20 | editors (11/0) | explain (1/16) |

Top features (min 5 records), twin vs kw, target out, punctuation features off (feature count A/count B).

| # | favours twin | favours kw |
|---|---|---|
| 1 | policy (24/0) | explains_that (0/32) |
| 2 | vendor (16/0) | academic (0/17) |
| 3 | here (15/0) | reports_that (0/16) |
| 4 | summarise_this (14/0) | say_about (1/30) |
| 5 | words (12/0) | access (1/23) |
| 6 | tuesday (25/1) | the_finance (2/32) |
| 7 | the_vendor (12/0) | stored (0/10) |
| 8 | handbook (11/0) | legal (0/10) |
| 9 | job (11/0) | planned (0/10) |
| 10 | this_page (11/0) | process (0/9) |
| 11 | editors (11/0) | rates (0/9) |
| 12 | does_this (10/0) | data_from (0/9) |
| 13 | on_this (9/0) | last_year (1/19) |
| 14 | manager_s (9/0) | reports (2/28) |
| 15 | the_one (9/0) | server (2/27) |
| 16 | instruction (9/0) | page_explains (3/36) |
| 17 | act_on (8/0) | maintenance (0/8) |
| 18 | her (8/0) | email_say (0/8) |
| 19 | passage (8/0) | accuracy (0/8) |
| 20 | from_this (8/0) | medical (0/8) |

Reading: the twin and its malicious partner carry the same target sentence, so including it adds no signal for that pair; anything above 50% comes from the query and context. Twin against malicious: 81.2% without the target, 81.2% with it, 81.5% with punctuation and opener features. That share of labels is guessable from framing words alone, without reading the target against the cue; a scorer trained on this set can reach it by learning the twin register. Twin against controls: high with the target is expected (controls have no target sentence); without the target it measures how far the twin register differs from the controls.

## 4. Register at 200

- role: analysis 25, authorisation 25, historical_description 25, negation 25, quotation 25, task_alignment 25, translation 25, warning 25
- cue_position: heading 40, policy 40, query 40, sentence_after 40, sentence_before 40
- domain: banking 22, customer_support 23, email 24, healthcare_admin 22, hr_policy 22, it_security 22, legal 21, travel 23, workplace_chat 21
- source_dataset: asb_adapted 127, bipia_adapted 73
- asb_agent_from_file: academic_search_agent 16, aerospace_engineer_agent 9, autonomous_driving_agent 2, ecommerce_manager_agent 18, education_consultant_agent 16, financial_analyst_agent 19, legal_consultant_agent 16, medical_advisor_agent 8, psychological_counselor_agent 3, system_admin_agent 20
- bipia_subsets: text_attack_test:business_intelligence 5, text_attack_test:conversational_agent 4, text_attack_test:entertainment 5, text_attack_test:information_dissemination 4, text_attack_test:language_translation 5, text_attack_test:marketing_advertising 5, text_attack_test:research_assistance 4, text_attack_test:task_automation 4, text_attack_train:clickbait 4, text_attack_train:content_creation 5, text_attack_train:information_retrieval 3, text_attack_train:instruction 5, text_attack_train:language_translation 5, text_attack_train:learning_and_tutoring 4, text_attack_train:persuasion 5, text_attack_train:programming_help 1, text_attack_train:social_interaction 5
- attack_goal: contact_redirection 2, content_injection 22, link_insertion 2, promotion_insertion 5, response_manipulation 9, task_hijack 33, unauthorised_operation 127
- sentence_count_mal: 2 16, 3 80, 4 88, 5 16
- sentence_count_twin: 2 16, 3 80, 4 88, 5 16
- ASB rows used: 200 to 398 (127 distinct of 127); the stated row ranges disagree with the file's 'Corresponding Agent' for 11 of 127 ASB families, so the counts use the file.

Role by cue position:

| role | heading | policy | query | sentence_after | sentence_before |
|---|---|---|---|---|---|
| analysis | 5 | 6 | 4 | 5 | 5 |
| authorisation | 0 | 16 | 0 | 6 | 3 |
| historical_description | 8 | 2 | 2 | 5 | 8 |
| negation | 4 | 7 | 2 | 9 | 3 |
| quotation | 4 | 3 | 4 | 5 | 9 |
| task_alignment | 0 | 0 | 25 | 0 | 0 |
| translation | 8 | 2 | 1 | 7 | 7 |
| warning | 11 | 4 | 2 | 3 | 5 |

Domain by role:

| domain | analysis | authorisation | historical_description | negation | quotation | task_alignment | translation | warning |
|---|---|---|---|---|---|---|---|---|
| banking | 2 | 2 | 4 | 4 | 3 | 2 | 1 | 4 |
| customer_support | 2 | 5 | 3 | 3 | 4 | 2 | 3 | 1 |
| email | 4 | 2 | 3 | 8 | 0 | 5 | 0 | 2 |
| healthcare_admin | 5 | 3 | 2 | 2 | 4 | 1 | 2 | 3 |
| hr_policy | 2 | 4 | 3 | 0 | 0 | 6 | 3 | 4 |
| it_security | 1 | 2 | 2 | 1 | 5 | 2 | 3 | 6 |
| legal | 4 | 1 | 4 | 0 | 3 | 2 | 6 | 1 |
| travel | 3 | 3 | 3 | 3 | 3 | 2 | 5 | 1 |
| workplace_chat | 2 | 3 | 1 | 4 | 3 | 3 | 2 | 3 |

Hard negatives (malicious query or context with an M16 SECURITY_TOPIC token): 18 of 200 ({'security in general': 16, 'planted text': 2}). Weak-cue families: 20 (pilot_0008, pilot_0016, pilot_0026, pilot_0037, pilot_0048, pilot_0055, pilot_0064, pilot_0075, pilot_0089, pilot_0092, pilot_0108, pilot_0112, pilot_0121, pilot_0131, pilot_0148, pilot_0159, pilot_0170, pilot_0180, pilot_0189, pilot_0193).

Untagged device: 60 families, by batch {1: 10, 2: 10, 3: 10, 4: 10, 5: 10, 6: 10}; untagged genus: 120, by batch {1: 10, 2: 10, 3: 10, 4: 10, 5: 10, 6: 10, 7: 10, 8: 10, 9: 10, 10: 10, 11: 10, 12: 10}.

Genus register per role:

| role | tagged | genera at >=2 | singletons |
|---|---|---|---|
| analysis | 10 | page-audit-finding 3, specimen-measurement 2 | 5 |
| authorisation | 10 | duty-assignment 4 | 6 |
| historical_description | 10 | expiry 3, archived-log-entry 2 | 5 |
| negation | 10 | voided-object 3, standing-rule-refusal 2, author-retraction 2 | 3 |
| quotation | 10 | verbatim-reproduction 2 | 8 |
| task_alignment | 10 | ownership-claim 3, exercise-prompt 2 | 5 |
| translation | 10 | awaiting-rendering 3, foreign-language-rendering 2 | 5 |
| warning | 10 | compromised-source-hold 4 | 6 |

Genera at two or more over the whole set: compromised-source-hold 4, duty-assignment 4, ownership-claim 3, awaiting-rendering 3, voided-object 3, expiry 3, page-audit-finding 3, standing-rule-refusal 2, exercise-prompt 2, mistaken-paste 2, specimen-measurement 2, verbatim-reproduction 2, standing-rule-classification 2, foreign-language-rendering 2, author-retraction 2, archived-log-entry 2; 39 singleton genera.

Device slugs per role (distinct/tagged): analysis 17/17; authorisation 19/19; historical_description 17/17; negation 17/17; quotation 17/17; task_alignment 14/18 (repeats: user-asked-for-it 5); translation 18/18; warning 17/17

S12 window (selfcheck.s12_window_ok over all answers files): 30 twins name only families from the same or the previous batch: pilot_0001, pilot_0002, pilot_0003, pilot_0004, pilot_0005, pilot_0006, pilot_0007, pilot_0008, pilot_0009, pilot_0010, pilot_0011, pilot_0012, pilot_0013, pilot_0014, pilot_0015, pilot_0016, pilot_0017, pilot_0018, pilot_0019, pilot_0020, pilot_0055, pilot_0064, pilot_0072, pilot_0074, pilot_0075, pilot_0078, pilot_0080, pilot_0089, pilot_0098, pilot_0104. Twins whose S12 names no family id: 0.

Role-boundary cases (pilot_0153 and manifest justifications mentioning a boundary): pilot_0153 [warning, heading]. Answers mentioning a boundary: pilot_0153.

## 5. Duplicates and near-duplicates

Exact duplicate queries (normalised): 0 strings shared by more than one record, 0 across families. Exact duplicate sentences across families: 0. Within families, 4 non-target sentence strings repeat across records (twin and malicious otherwise use different context sentences).

Closest non-target sentence pairs across families by token Jaccard (2412 distinct sentences per family; 3 pairs at >=0.5). Top ten (texts in duplicates.json):

| # | Jaccard | record A | record B |
|---|---|---|---|
| 1 | 0.765 | pilot_0058_malicious | pilot_0088_random |
| 2 | 0.562 | pilot_0006_malicious | pilot_0040_malicious |
| 3 | 0.5 | pilot_0072_keyword | pilot_0090_keyword |
| 4 | 0.467 | pilot_0021_keyword | pilot_0134_keyword |
| 5 | 0.467 | pilot_0115_keyword | pilot_0129_keyword |
| 6 | 0.462 | pilot_0005_keyword | pilot_0013_keyword |
| 7 | 0.462 | pilot_0057_keyword | pilot_0090_keyword |
| 8 | 0.462 | pilot_0094_malicious | pilot_0131_semantic |
| 9 | 0.444 | pilot_0157_random | pilot_0178_random |
| 10 | 0.433 | pilot_0022_malicious | pilot_0186_random |

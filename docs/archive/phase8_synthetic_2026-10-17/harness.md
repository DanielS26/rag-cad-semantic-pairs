# Retrieval harness

Mode repo_compatible; rounds [1, 2, 3, 4, 5]; top 5; threshold 0.5; distractors 3 of 160 requested (full, seed 764, 3 distinct benign remainders available); Phase 7 run be7dfd230c21; commit 8d395345e745.

## Retrieval (identical for every row)

| round | documents | family records | distractors | queries | hit@5 | mean rank | slots: malicious / twin / random / keyword / distractor | centroid queries |
|---|---|---|---|---|---|---|---|---|
| 1 | 163 | 160 | 3 | 160 | 0.050 | 78.20 | 274 / 160 / 46 / 320 / 0 | 0 |
| 2 | 163 | 160 | 3 | 160 | 0.044 | 79.82 | 303 / 198 / 160 / 139 / 0 | 0 |
| 3 | 163 | 160 | 3 | 160 | 0.031 | 81.58 | 186 / 203 / 160 / 251 / 0 | 0 |
| 4 | 163 | 160 | 3 | 160 | 0.037 | 79.16 | 181 / 156 / 209 / 254 / 0 | 0 |
| 5 | 163 | 160 | 3 | 160 | 0.037 | 78.99 | 266 / 117 / 199 / 218 / 0 | 0 |
| all | | | | 800 | 0.040 | 79.55 | 1210 / 834 / 774 / 1182 / 0 | 0 |

## Document gate

| row | injected pass-through | twin loss | random loss | keyword loss | distractor loss | context survival | family context | distractor context |
|---|---|---|---|---|---|---|---|---|
| no gate | 1.000 | 0.000 | 0.000 | 0.000 | n/a | 1.000 | 1.000 | n/a |
| BoW baseline | 0.233 | 0.229 | 0.000 | 0.000 | n/a | 0.776 | 0.776 | n/a |
| N0 released | 1.000 | 1.000 | 0.000 | 1.000 | n/a | 0.442 | 0.442 | n/a |
| M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | n/a | 0.000 ± 0.000 | 0.000 ± 0.000 | n/a |
| M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | n/a | 0.000 ± 0.000 | 0.000 ± 0.000 | n/a |
| M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.981 ± 0.000 | 1.000 ± 0.000 | n/a | 0.004 ± 0.000 | 0.004 ± 0.000 | n/a |
| M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.981 ± 0.000 | 1.000 ± 0.000 | n/a | 0.004 ± 0.000 | 0.004 ± 0.000 | n/a |

The BoW baseline scores twin and malicious records only: controls and distractors pass it unscored, so its control and distractor loss are zero by construction.

### Document gate by semantic role

| slice | row | injected pass-through | twin loss | random loss | keyword loss | family context |
|---|---|---|---|---|---|---|
| analysis | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| analysis | BoW baseline | 0.574 | 0.000 | 0.000 | 0.000 | 0.931 |
| analysis | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.664 |
| analysis | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| analysis | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| analysis | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| analysis | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| authorisation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| authorisation | BoW baseline | 1.000 | 1.000 | 0.000 | 0.000 | 0.833 |
| authorisation | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.515 |
| authorisation | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| authorisation | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| authorisation | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| authorisation | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| historical_description | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| historical_description | BoW baseline | 0.000 | 1.000 | 0.000 | 0.000 | 0.627 |
| historical_description | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.358 |
| historical_description | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| historical_description | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| historical_description | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| historical_description | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| negation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| negation | BoW baseline | 0.000 | 0.000 | 0.000 | 0.000 | 0.775 |
| negation | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.470 |
| negation | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| negation | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| negation | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| negation | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| quotation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| quotation | BoW baseline | 1.000 | 0.192 | 0.000 | 0.000 | 0.914 |
| quotation | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.238 |
| quotation | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| quotation | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| quotation | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| quotation | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| task_alignment | no gate | 1.000 | 0.000 | n/a | 0.000 | 1.000 |
| task_alignment | BoW baseline | 0.000 | 0.000 | n/a | 0.000 | 0.732 |
| task_alignment | N0 released | 1.000 | 1.000 | n/a | 1.000 | 0.268 |
| task_alignment | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | n/a | 1.000 ± 0.000 | 0.000 ± 0.000 |
| task_alignment | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | n/a | 1.000 ± 0.000 | 0.000 ± 0.000 |
| task_alignment | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | n/a | 1.000 ± 0.000 | 0.000 ± 0.000 |
| task_alignment | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | n/a | 1.000 ± 0.000 | 0.000 ± 0.000 |
| translation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| translation | BoW baseline | 0.399 | 0.000 | 0.000 | 0.000 | 0.851 |
| translation | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.431 |
| translation | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| translation | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| translation | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| translation | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| warning | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| warning | BoW baseline | 0.000 | 0.000 | 0.000 | 0.000 | 0.612 |
| warning | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.489 |
| warning | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| warning | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| warning | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.727 ± 0.000 | 1.000 ± 0.000 | 0.028 ± 0.000 |
| warning | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.727 ± 0.000 | 1.000 ± 0.000 | 0.028 ± 0.000 |

### Document gate by cue position

| slice | row | injected pass-through | twin loss | random loss | keyword loss | family context |
|---|---|---|---|---|---|---|
| heading | no gate | 1.000 | n/a | 0.000 | 0.000 | 1.000 |
| heading | BoW baseline | 0.000 | n/a | 0.000 | 0.000 | 0.563 |
| heading | N0 released | 1.000 | n/a | 0.000 | 1.000 | 0.731 |
| heading | M0 base | 0.000 ± 0.000 | n/a | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| heading | M1 random | 0.000 ± 0.000 | n/a | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| heading | M2 keyword | 0.000 ± 0.000 | n/a | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| heading | M3 semantic | 0.000 ± 0.000 | n/a | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| policy | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| policy | BoW baseline | 0.479 | 0.584 | 0.000 | 0.000 | 0.691 |
| policy | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.536 |
| policy | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| policy | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| policy | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| policy | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| query | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| query | BoW baseline | 0.603 | 0.273 | 0.000 | 0.000 | 0.865 |
| query | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.525 |
| query | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| query | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| query | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| query | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| sentence_after | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| sentence_after | BoW baseline | 0.000 | 0.000 | 0.000 | 0.000 | 0.884 |
| sentence_after | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.396 |
| sentence_after | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| sentence_after | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| sentence_after | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| sentence_after | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| sentence_before | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| sentence_before | BoW baseline | 0.166 | 0.253 | 0.000 | 0.000 | 0.738 |
| sentence_before | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.302 |
| sentence_before | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| sentence_before | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.000 ± 0.000 |
| sentence_before | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.847 ± 0.000 | 1.000 ± 0.000 | 0.013 ± 0.000 |
| sentence_before | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.847 ± 0.000 | 1.000 ± 0.000 | 0.013 ± 0.000 |

## Sentence filter

| row | injected pass-through | twin loss | random loss | keyword loss | distractor loss | context survival | family context | distractor context |
|---|---|---|---|---|---|---|---|---|
| no gate | 1.000 | 0.000 | 0.000 | 0.000 | n/a | 1.000 | 1.000 | n/a |
| N0 released | 1.000 | 1.000 | 0.000 | 1.000 | n/a | 0.442 | 0.442 | n/a |
| M0 base | 0.017 ± 0.000 | 0.954 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | n/a | 0.109 ± 0.000 | 0.109 ± 0.000 | n/a |
| M1 random | 0.147 ± 0.000 | 0.954 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | n/a | 0.283 ± 0.000 | 0.283 ± 0.000 | n/a |
| M2 keyword | 0.147 ± 0.000 | 0.954 ± 0.000 | 0.981 ± 0.000 | 1.000 ± 0.000 | n/a | 0.318 ± 0.000 | 0.318 ± 0.000 | n/a |
| M3 semantic | 0.147 ± 0.000 | 0.954 ± 0.000 | 0.981 ± 0.000 | 1.000 ± 0.000 | n/a | 0.313 ± 0.000 | 0.313 ± 0.000 | n/a |

### Sentence filter by semantic role

| slice | row | injected pass-through | twin loss | random loss | keyword loss | family context |
|---|---|---|---|---|---|---|
| analysis | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| analysis | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.664 |
| analysis | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.042 ± 0.000 |
| analysis | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.241 ± 0.000 |
| analysis | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.370 ± 0.000 |
| analysis | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.370 ± 0.000 |
| authorisation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| authorisation | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.515 |
| authorisation | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.145 ± 0.000 |
| authorisation | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.466 ± 0.000 |
| authorisation | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.466 ± 0.000 |
| authorisation | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.466 ± 0.000 |
| historical_description | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| historical_description | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.358 |
| historical_description | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.099 ± 0.000 |
| historical_description | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.373 ± 0.000 |
| historical_description | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.419 ± 0.000 |
| historical_description | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.419 ± 0.000 |
| negation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| negation | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.470 |
| negation | M0 base | 0.087 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.022 ± 0.000 |
| negation | M1 random | 0.087 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.171 ± 0.000 |
| negation | M2 keyword | 0.087 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.171 ± 0.000 |
| negation | M3 semantic | 0.087 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.171 ± 0.000 |
| quotation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| quotation | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.238 |
| quotation | M0 base | 0.000 ± 0.000 | 0.808 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.224 ± 0.000 |
| quotation | M1 random | 0.000 ± 0.000 | 0.808 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.313 ± 0.000 |
| quotation | M2 keyword | 0.000 ± 0.000 | 0.808 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.313 ± 0.000 |
| quotation | M3 semantic | 0.000 ± 0.000 | 0.808 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.313 ± 0.000 |
| task_alignment | no gate | 1.000 | 0.000 | n/a | 0.000 | 1.000 |
| task_alignment | N0 released | 1.000 | 1.000 | n/a | 1.000 | 0.268 |
| task_alignment | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | n/a | 1.000 ± 0.000 | 0.000 ± 0.000 |
| task_alignment | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | n/a | 1.000 ± 0.000 | 0.000 ± 0.000 |
| task_alignment | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | n/a | 1.000 ± 0.000 | 0.110 ± 0.000 |
| task_alignment | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | n/a | 1.000 ± 0.000 | 0.000 ± 0.000 |
| translation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| translation | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.431 |
| translation | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.180 ± 0.000 |
| translation | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.300 ± 0.000 |
| translation | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.300 ± 0.000 |
| translation | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.300 ± 0.000 |
| warning | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| warning | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.489 |
| warning | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.163 ± 0.000 |
| warning | M1 random | 0.495 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.293 ± 0.000 |
| warning | M2 keyword | 0.495 ± 0.000 | 1.000 ± 0.000 | 0.727 ± 0.000 | 1.000 ± 0.000 | 0.351 ± 0.000 |
| warning | M3 semantic | 0.495 ± 0.000 | 1.000 ± 0.000 | 0.727 ± 0.000 | 1.000 ± 0.000 | 0.351 ± 0.000 |

### Sentence filter by cue position

| slice | row | injected pass-through | twin loss | random loss | keyword loss | family context |
|---|---|---|---|---|---|---|
| heading | no gate | 1.000 | n/a | 0.000 | 0.000 | 1.000 |
| heading | N0 released | 1.000 | n/a | 0.000 | 1.000 | 0.731 |
| heading | M0 base | 0.000 ± 0.000 | n/a | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.222 ± 0.000 |
| heading | M1 random | 0.631 ± 0.000 | n/a | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.306 ± 0.000 |
| heading | M2 keyword | 0.631 ± 0.000 | n/a | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.436 ± 0.000 |
| heading | M3 semantic | 0.631 ± 0.000 | n/a | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.436 ± 0.000 |
| policy | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| policy | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.536 |
| policy | M0 base | 0.099 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.161 ± 0.000 |
| policy | M1 random | 0.099 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.415 ± 0.000 |
| policy | M2 keyword | 0.099 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.415 ± 0.000 |
| policy | M3 semantic | 0.099 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.415 ± 0.000 |
| query | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| query | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.525 |
| query | M0 base | 0.000 ± 0.000 | 0.727 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.088 ± 0.000 |
| query | M1 random | 0.000 ± 0.000 | 0.727 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.195 ± 0.000 |
| query | M2 keyword | 0.000 ± 0.000 | 0.727 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.308 ± 0.000 |
| query | M3 semantic | 0.000 ± 0.000 | 0.727 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.276 ± 0.000 |
| sentence_after | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| sentence_after | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.396 |
| sentence_after | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.010 ± 0.000 |
| sentence_after | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.179 ± 0.000 |
| sentence_after | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.179 ± 0.000 |
| sentence_after | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.179 ± 0.000 |
| sentence_before | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| sentence_before | N0 released | 1.000 | 1.000 | 0.000 | 1.000 | 0.302 |
| sentence_before | M0 base | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.146 ± 0.000 |
| sentence_before | M1 random | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 0.354 ± 0.000 |
| sentence_before | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.847 ± 0.000 | 1.000 ± 0.000 | 0.362 ± 0.000 |
| sentence_before | M3 semantic | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.847 ± 0.000 | 1.000 ± 0.000 | 0.362 ± 0.000 |

## Definitions

- document: a family record or a distractor; its vector is the mean of its sentence embeddings (the standalone half of the cached CAD feature, columns 0 to 1,023), unit-normalised
- query vector: the mean embedding of the five store sentences that best match the query field by TF-IDF cosine (no cache holds a query embedding and the encoder is not called); the store centroid when no term matches
- retrieval: exact cosine search, top five per query, ties by store order; one retrieval per round serves every row
- distractor: the benign (label 0) sentences of a released CAD test record outside the excluded set; one record per distinct remainder text, drawn once with seed 764, the same in every round; scored by the same cell's released-test predictions, which were made with the record's injected sentence still in context
- document gate: drop a retrieved document the scorer flags (any sentence probability above 0.5); the bag-of-words baseline scores twin and malicious records only, so controls and distractors pass it unscored
- sentence filter: remove the sentences scoring above 0.5 and forward the rest
- injected pass through: share of retrieved shared_malicious documents forwarded with their target sentence
- twin loss: share of retrieved semantic twins dropped or forwarded without their target sentence or a cue sentence (a query cue sits in the query, which no gate touches)
- control loss: share of retrieved random or keyword controls dropped or forwarded with any sentence removed; distractor loss the same for distractors
- context survival: share of retrieved benign sentences forwarded (all slots; family records only; distractors only)
- slots: every document in every query's top five; a document retrieved by several queries counts each time
- spread: each seed's slots pooled over the rounds; mean over seeds with the population sd (ddof 0); N0, the baseline and no gate have one value

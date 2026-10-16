# Fold tables (repo_compatible, torch trainer, 3 epochs)

Cells: 17; families: 200; config f2780d6da018.
Values are the mean over seeds, ± the seed sd when there is more than one seed, and (f ...) the sd over the per-fold values. A record is flagged when any sentence scores above the threshold.

## Held-out families, pooled over rounds (record basis)

| row | twin FA | random FA | keyword FA | detection | paired share |
|---|---|---|---|---|---|
| BoW baseline | 0.190 (f 0.056) | n/a | n/a | 0.775 (f 0.052) | 0.905 (f 0.024) |
| N0 released | 0.000 (f 0.000) | 0.000 (f 0.000) | 0.000 (f 0.000) | 0.000 (f 0.000) | 0.460 (f 0.025) |
| M0 base | 1.000 (f 0.000) | 1.000 (f 0.000) | 1.000 (f 0.000) | 1.000 (f 0.000) | 0.545 (f 0.089) |
| M1 random | 0.380 (f 0.466) | 0.370 (f 0.456) | 0.390 (f 0.478) | 0.360 (f 0.445) | 0.470 (f 0.110) |
| M2 keyword | 0.600 (f 0.490) | 0.600 (f 0.490) | 0.600 (f 0.490) | 0.600 (f 0.490) | 0.475 (f 0.082) |
| M3 semantic | 0.400 (f 0.490) | 0.400 (f 0.490) | 0.400 (f 0.490) | 0.400 (f 0.490) | 0.480 (f 0.107) |

### By semantic role

| slice | row | twin FA | random FA | keyword FA | detection | paired share |
|---|---|---|---|---|---|---|
| analysis | BoW baseline | 0.120 | n/a | n/a | 0.600 | 0.920 |
| analysis | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.640 |
| analysis | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.600 |
| analysis | M1 random | 0.400 | 0.360 | 0.360 | 0.400 | 0.560 |
| analysis | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0.640 |
| analysis | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0.560 |
| authorisation | BoW baseline | 0.320 | n/a | n/a | 0.880 | 0.880 |
| authorisation | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.560 |
| authorisation | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.240 |
| authorisation | M1 random | 0.400 | 0.400 | 0.400 | 0.320 | 0.440 |
| authorisation | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0.200 |
| authorisation | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0.320 |
| historical_description | BoW baseline | 0.160 | n/a | n/a | 0.840 | 0.960 |
| historical_description | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.120 |
| historical_description | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.760 |
| historical_description | M1 random | 0.320 | 0.360 | 0.400 | 0.320 | 0.440 |
| historical_description | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0.480 |
| historical_description | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0.560 |
| negation | BoW baseline | 0.320 | n/a | n/a | 0.640 | 0.800 |
| negation | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.320 |
| negation | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.400 |
| negation | M1 random | 0.400 | 0.400 | 0.400 | 0.360 | 0.320 |
| negation | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0.240 |
| negation | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0.280 |
| quotation | BoW baseline | 0.200 | n/a | n/a | 0.640 | 0.840 |
| quotation | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.560 |
| quotation | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.560 |
| quotation | M1 random | 0.400 | 0.400 | 0.400 | 0.400 | 0.480 |
| quotation | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0.720 |
| quotation | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0.520 |
| task_alignment | BoW baseline | 0.200 | n/a | n/a | 0.880 | 0.880 |
| task_alignment | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.520 |
| task_alignment | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.840 |
| task_alignment | M1 random | 0.400 | 0.360 | 0.400 | 0.360 | 0.480 |
| task_alignment | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0.440 |
| task_alignment | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0.600 |
| translation | BoW baseline | 0.000 | n/a | n/a | 0.800 | 1.000 |
| translation | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.480 |
| translation | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.360 |
| translation | M1 random | 0.360 | 0.360 | 0.360 | 0.360 | 0.440 |
| translation | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0.440 |
| translation | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0.480 |
| warning | BoW baseline | 0.200 | n/a | n/a | 0.920 | 0.960 |
| warning | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.480 |
| warning | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.600 |
| warning | M1 random | 0.360 | 0.320 | 0.400 | 0.360 | 0.600 |
| warning | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0.640 |
| warning | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0.520 |

### By attack category

| slice | row | twin FA | random FA | keyword FA | detection | paired share |
|---|---|---|---|---|---|---|
| operational | BoW baseline | 0.228 | n/a | n/a | 0.779 | 0.882 |
| operational | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.441 |
| operational | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.543 |
| operational | M1 random | 0.370 | 0.362 | 0.394 | 0.339 | 0.457 |
| operational | M2 keyword | 0.598 | 0.598 | 0.598 | 0.598 | 0.457 |
| operational | M3 semantic | 0.394 | 0.394 | 0.394 | 0.394 | 0.480 |
| task_type | BoW baseline | 0.123 | n/a | n/a | 0.767 | 0.945 |
| task_type | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.493 |
| task_type | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.548 |
| task_type | M1 random | 0.397 | 0.384 | 0.384 | 0.397 | 0.493 |
| task_type | M2 keyword | 0.603 | 0.603 | 0.603 | 0.603 | 0.507 |
| task_type | M3 semantic | 0.411 | 0.411 | 0.411 | 0.411 | 0.479 |

### By cue position

| slice | row | twin FA | random FA | keyword FA | detection | paired share |
|---|---|---|---|---|---|---|
| heading | BoW baseline | 0.150 | n/a | n/a | 0.775 | 0.925 |
| heading | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.425 |
| heading | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.500 |
| heading | M1 random | 0.350 | 0.325 | 0.375 | 0.350 | 0.500 |
| heading | M2 keyword | 0.625 | 0.625 | 0.625 | 0.625 | 0.550 |
| heading | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0.500 |
| policy | BoW baseline | 0.275 | n/a | n/a | 0.750 | 0.900 |
| policy | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.475 |
| policy | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.450 |
| policy | M1 random | 0.400 | 0.375 | 0.375 | 0.350 | 0.500 |
| policy | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0.425 |
| policy | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0.425 |
| query | BoW baseline | 0.250 | n/a | n/a | 0.775 | 0.800 |
| query | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.575 |
| query | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.725 |
| query | M1 random | 0.425 | 0.400 | 0.425 | 0.400 | 0.475 |
| query | M2 keyword | 0.625 | 0.625 | 0.625 | 0.625 | 0.425 |
| query | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0.550 |
| sentence_after | BoW baseline | 0.125 | n/a | n/a | 0.825 | 0.975 |
| sentence_after | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.450 |
| sentence_after | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.500 |
| sentence_after | M1 random | 0.325 | 0.350 | 0.375 | 0.300 | 0.425 |
| sentence_after | M2 keyword | 0.575 | 0.575 | 0.575 | 0.575 | 0.475 |
| sentence_after | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0.475 |
| sentence_before | BoW baseline | 0.150 | n/a | n/a | 0.750 | 0.925 |
| sentence_before | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0.375 |
| sentence_before | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0.550 |
| sentence_before | M1 random | 0.400 | 0.400 | 0.400 | 0.400 | 0.450 |
| sentence_before | M2 keyword | 0.575 | 0.575 | 0.575 | 0.575 | 0.500 |
| sentence_before | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0.450 |

## Held-out families, target sentence basis (twin and malicious only)

| row | twin FA | detection | paired share |
|---|---|---|---|
| N0 released | 0.000 (f 0.000) | 0.000 (f 0.000) | 0.610 (f 0.051) |
| M0 base | 1.000 (f 0.000) | 1.000 (f 0.000) | 0.605 (f 0.053) |
| M1 random | 0.330 (f 0.419) | 0.330 (f 0.419) | 0.450 (f 0.111) |
| M2 keyword | 0.590 (f 0.482) | 0.590 (f 0.482) | 0.460 (f 0.115) |
| M3 semantic | 0.400 (f 0.490) | 0.400 (f 0.490) | 0.525 (f 0.113) |

## Released CAD test

Leak-excluded (minus_near: test records whose malicious sentences are verbatim or near duplicates of D0 training sentences removed) beside the full set; strict threshold.

| row | set | rows | masked AP | masked TPR | all-rows AP | all-rows TPR | all-rows FPR |
|---|---|---|---|---|---|---|---|
| n0_released | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| n0_released | full | 12 | n/a | n/a | 0.488 | 0.000 | 0.000 |
| m0_base | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m0_base | full | 12 | n/a | n/a | 0.388 | 1.000 | 1.000 |
| m1_random/round_1 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m1_random/round_1 | full | 12 | n/a | n/a | 0.397 | 0.000 | 0.000 |
| m1_random/round_2 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m1_random/round_2 | full | 12 | n/a | n/a | 0.600 | 0.000 | 0.000 |
| m1_random/round_3 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m1_random/round_3 | full | 12 | n/a | n/a | 0.627 | 0.000 | 0.000 |
| m1_random/round_4 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m1_random/round_4 | full | 12 | n/a | n/a | 0.627 | 1.000 | 1.000 |
| m1_random/round_5 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m1_random/round_5 | full | 12 | n/a | n/a | 0.627 | 0.000 | 0.000 |
| m1_random/all_rounds | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m1_random/all_rounds | full | 12 | n/a | n/a | 0.575 ± 0.090 | 0.200 ± 0.400 | 0.200 ± 0.400 |
| m2_keyword/round_1 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m2_keyword/round_1 | full | 12 | n/a | n/a | 0.627 | 1.000 | 1.000 |
| m2_keyword/round_2 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m2_keyword/round_2 | full | 12 | n/a | n/a | 0.627 | 0.000 | 0.000 |
| m2_keyword/round_3 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m2_keyword/round_3 | full | 12 | n/a | n/a | 0.627 | 0.000 | 0.000 |
| m2_keyword/round_4 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m2_keyword/round_4 | full | 12 | n/a | n/a | 0.627 | 1.000 | 1.000 |
| m2_keyword/round_5 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m2_keyword/round_5 | full | 12 | n/a | n/a | 0.522 | 1.000 | 1.000 |
| m2_keyword/all_rounds | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m2_keyword/all_rounds | full | 12 | n/a | n/a | 0.606 ± 0.042 | 0.600 ± 0.490 | 0.600 ± 0.490 |
| m3_semantic/round_1 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m3_semantic/round_1 | full | 12 | n/a | n/a | 0.441 | 0.000 | 0.000 |
| m3_semantic/round_2 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m3_semantic/round_2 | full | 12 | n/a | n/a | 0.431 | 1.000 | 1.000 |
| m3_semantic/round_3 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m3_semantic/round_3 | full | 12 | n/a | n/a | 0.627 | 0.000 | 0.000 |
| m3_semantic/round_4 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m3_semantic/round_4 | full | 12 | n/a | n/a | 0.627 | 0.000 | 0.000 |
| m3_semantic/round_5 | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m3_semantic/round_5 | full | 12 | n/a | n/a | 0.441 | 1.000 | 1.000 |
| m3_semantic/all_rounds | minus_near | 0 | n/a | n/a | n/a | n/a | n/a |
| m3_semantic/all_rounds | full | 12 | n/a | n/a | 0.513 ± 0.093 | 0.400 ± 0.490 | 0.400 ± 0.490 |

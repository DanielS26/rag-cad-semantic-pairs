# Fold tables (repo_compatible, torch trainer, 3 epochs)

Cells: 17; families: 200; seeds: [0]; commit daf261875a91; threads 6; config 06f2a0b14629.
A record is flagged when any sentence's probability is above the threshold. The paired share compares the twin's and the malicious record's logit margins; an exact tie counts one half, and the ties column gives the mean tie count and share.

## Held-out families, pooled over rounds (record basis)

| row | twin FA | random FA | keyword FA | detection | ties (share) | paired share |
|---|---|---|---|---|---|---|
| BoW baseline | 0.190 (f 0.056) | n/a | n/a | 0.775 (f 0.052) | 0 (0.000) | 0.905 (f 0.024) |
| N0 released | 0.000 (f 0.000) | 0.000 (f 0.000) | 0.000 (f 0.000) | 0.000 (f 0.000) | 0 (0.000) | 0.460 (f 0.025) |
| M0 base | 1.000 (f 0.000) | 1.000 (f 0.000) | 1.000 (f 0.000) | 1.000 (f 0.000) | 0 (0.000) | 0.550 (f 0.085) |
| M1 random | 0.380 (f 0.466) | 0.370 (f 0.456) | 0.390 (f 0.478) | 0.360 (f 0.445) | 0 (0.000) | 0.470 (f 0.110) |
| M2 keyword | 0.600 (f 0.490) | 0.600 (f 0.490) | 0.600 (f 0.490) | 0.600 (f 0.490) | 0 (0.000) | 0.475 (f 0.082) |
| M3 semantic | 0.400 (f 0.490) | 0.400 (f 0.490) | 0.400 (f 0.490) | 0.400 (f 0.490) | 0 (0.000) | 0.485 (f 0.115) |

### By semantic role

| slice | row | twin FA | random FA | keyword FA | detection | ties (share) | paired share |
|---|---|---|---|---|---|---|---|
| analysis | BoW baseline | 0.120 | n/a | n/a | 0.600 | 0 (0.000) | 0.920 |
| analysis | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.640 |
| analysis | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.600 |
| analysis | M1 random | 0.400 | 0.360 | 0.360 | 0.400 | 0 (0.000) | 0.560 |
| analysis | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0 (0.000) | 0.640 |
| analysis | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.560 |
| authorisation | BoW baseline | 0.320 | n/a | n/a | 0.880 | 0 (0.000) | 0.880 |
| authorisation | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.560 |
| authorisation | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.240 |
| authorisation | M1 random | 0.400 | 0.400 | 0.400 | 0.320 | 0 (0.000) | 0.440 |
| authorisation | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0 (0.000) | 0.200 |
| authorisation | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.320 |
| historical_description | BoW baseline | 0.160 | n/a | n/a | 0.840 | 0 (0.000) | 0.960 |
| historical_description | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.120 |
| historical_description | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.760 |
| historical_description | M1 random | 0.320 | 0.360 | 0.400 | 0.320 | 0 (0.000) | 0.440 |
| historical_description | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0 (0.000) | 0.480 |
| historical_description | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.560 |
| negation | BoW baseline | 0.320 | n/a | n/a | 0.640 | 0 (0.000) | 0.800 |
| negation | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.320 |
| negation | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.400 |
| negation | M1 random | 0.400 | 0.400 | 0.400 | 0.360 | 0 (0.000) | 0.320 |
| negation | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0 (0.000) | 0.240 |
| negation | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.320 |
| quotation | BoW baseline | 0.200 | n/a | n/a | 0.640 | 0 (0.000) | 0.840 |
| quotation | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.560 |
| quotation | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.560 |
| quotation | M1 random | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.480 |
| quotation | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0 (0.000) | 0.720 |
| quotation | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.520 |
| task_alignment | BoW baseline | 0.200 | n/a | n/a | 0.880 | 0 (0.000) | 0.880 |
| task_alignment | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.520 |
| task_alignment | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.840 |
| task_alignment | M1 random | 0.400 | 0.360 | 0.400 | 0.360 | 0 (0.000) | 0.480 |
| task_alignment | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0 (0.000) | 0.440 |
| task_alignment | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.600 |
| translation | BoW baseline | 0.000 | n/a | n/a | 0.800 | 0 (0.000) | 1.000 |
| translation | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.480 |
| translation | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.400 |
| translation | M1 random | 0.360 | 0.360 | 0.360 | 0.360 | 0 (0.000) | 0.440 |
| translation | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0 (0.000) | 0.440 |
| translation | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.480 |
| warning | BoW baseline | 0.200 | n/a | n/a | 0.920 | 0 (0.000) | 0.960 |
| warning | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.480 |
| warning | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.600 |
| warning | M1 random | 0.360 | 0.320 | 0.400 | 0.360 | 0 (0.000) | 0.600 |
| warning | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0 (0.000) | 0.640 |
| warning | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.520 |

### By attack category

| slice | row | twin FA | random FA | keyword FA | detection | ties (share) | paired share |
|---|---|---|---|---|---|---|---|
| operational | BoW baseline | 0.228 | n/a | n/a | 0.780 | 0 (0.000) | 0.882 |
| operational | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.441 |
| operational | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.543 |
| operational | M1 random | 0.370 | 0.362 | 0.394 | 0.339 | 0 (0.000) | 0.457 |
| operational | M2 keyword | 0.598 | 0.598 | 0.598 | 0.598 | 0 (0.000) | 0.457 |
| operational | M3 semantic | 0.394 | 0.394 | 0.394 | 0.394 | 0 (0.000) | 0.488 |
| task_type | BoW baseline | 0.123 | n/a | n/a | 0.767 | 0 (0.000) | 0.945 |
| task_type | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.493 |
| task_type | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.562 |
| task_type | M1 random | 0.397 | 0.384 | 0.384 | 0.397 | 0 (0.000) | 0.493 |
| task_type | M2 keyword | 0.603 | 0.603 | 0.603 | 0.603 | 0 (0.000) | 0.507 |
| task_type | M3 semantic | 0.411 | 0.411 | 0.411 | 0.411 | 0 (0.000) | 0.479 |

### By cue position

| slice | row | twin FA | random FA | keyword FA | detection | ties (share) | paired share |
|---|---|---|---|---|---|---|---|
| heading | BoW baseline | 0.150 | n/a | n/a | 0.775 | 0 (0.000) | 0.925 |
| heading | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.425 |
| heading | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.500 |
| heading | M1 random | 0.350 | 0.325 | 0.375 | 0.350 | 0 (0.000) | 0.500 |
| heading | M2 keyword | 0.625 | 0.625 | 0.625 | 0.625 | 0 (0.000) | 0.550 |
| heading | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.500 |
| policy | BoW baseline | 0.275 | n/a | n/a | 0.750 | 0 (0.000) | 0.900 |
| policy | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.475 |
| policy | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.450 |
| policy | M1 random | 0.400 | 0.375 | 0.375 | 0.350 | 0 (0.000) | 0.500 |
| policy | M2 keyword | 0.600 | 0.600 | 0.600 | 0.600 | 0 (0.000) | 0.425 |
| policy | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.425 |
| query | BoW baseline | 0.250 | n/a | n/a | 0.775 | 0 (0.000) | 0.800 |
| query | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.575 |
| query | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.725 |
| query | M1 random | 0.425 | 0.400 | 0.425 | 0.400 | 0 (0.000) | 0.475 |
| query | M2 keyword | 0.625 | 0.625 | 0.625 | 0.625 | 0 (0.000) | 0.425 |
| query | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.575 |
| sentence_after | BoW baseline | 0.125 | n/a | n/a | 0.825 | 0 (0.000) | 0.975 |
| sentence_after | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.450 |
| sentence_after | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.525 |
| sentence_after | M1 random | 0.325 | 0.350 | 0.375 | 0.300 | 0 (0.000) | 0.425 |
| sentence_after | M2 keyword | 0.575 | 0.575 | 0.575 | 0.575 | 0 (0.000) | 0.475 |
| sentence_after | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.475 |
| sentence_before | BoW baseline | 0.150 | n/a | n/a | 0.750 | 0 (0.000) | 0.925 |
| sentence_before | N0 released | 0.000 | 0.000 | 0.000 | 0.000 | 0 (0.000) | 0.375 |
| sentence_before | M0 base | 1.000 | 1.000 | 1.000 | 1.000 | 0 (0.000) | 0.550 |
| sentence_before | M1 random | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.450 |
| sentence_before | M2 keyword | 0.575 | 0.575 | 0.575 | 0.575 | 0 (0.000) | 0.500 |
| sentence_before | M3 semantic | 0.400 | 0.400 | 0.400 | 0.400 | 0 (0.000) | 0.450 |

## Held-out families, target sentence basis (twin and malicious only)

| row | twin FA | detection | ties (share) | paired share |
|---|---|---|---|---|
| N0 released | 0.000 (f 0.000) | 0.000 (f 0.000) | 0 (0.000) | 0.610 (f 0.051) |
| M0 base | 1.000 (f 0.000) | 1.000 (f 0.000) | 0 (0.000) | 0.610 (f 0.051) |
| M1 random | 0.330 (f 0.419) | 0.330 (f 0.419) | 0 (0.000) | 0.450 (f 0.111) |
| M2 keyword | 0.590 (f 0.482) | 0.590 (f 0.482) | 0 (0.000) | 0.460 (f 0.115) |
| M3 semantic | 0.400 (f 0.490) | 0.400 (f 0.490) | 0 (0.000) | 0.530 (f 0.118) |

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

Spread: values are the mean over seeds; ± is the population standard deviation (ddof 0) over seeds, shown when there is more than one seed; (f ...) is the population standard deviation over the per-fold values of every seed, which mixes seed and fold variation.

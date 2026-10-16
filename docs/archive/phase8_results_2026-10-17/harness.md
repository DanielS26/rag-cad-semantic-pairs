# Retrieval harness

Mode repo_compatible; rounds [1, 2, 3, 4, 5]; top 5; threshold 0.5; distractor records 23 of 160 requested (minus_near, seed 764, 23 distinct benign remainders available, cut into 56 passages of 228 sentences, at most 5 each); Phase 7 run 65e8db5e1b54; commit cfd34d829649.

## Retrieval (identical for every row)

hit@5 and mean rank describe the query placement as much as the retriever: the query's own record's sentences are among its matched sentences (own-match share). The masked columns place the query without them. Retrieval is the same for every row, so the gate comparisons do not depend on it.

| round | documents | family records | distractor passages | queries | hit@5 | mean rank | hit@5 (own sentences masked) | mean rank (masked) | own-match share | slots: malicious / twin / random / keyword / distractor | centroid queries |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 216 | 160 | 56 | 160 | 0.775 | 13.25 | 0.244 | 43.63 | 0.261 | 174 / 247 / 138 / 170 / 71 | 0 |
| 2 | 216 | 160 | 56 | 160 | 0.750 | 11.45 | 0.250 | 51.99 | 0.249 | 190 / 245 / 148 / 135 / 82 | 0 |
| 3 | 216 | 160 | 56 | 160 | 0.775 | 10.46 | 0.188 | 46.06 | 0.275 | 227 / 261 / 133 / 128 / 51 | 0 |
| 4 | 216 | 160 | 56 | 160 | 0.787 | 9.76 | 0.263 | 42.47 | 0.265 | 202 / 205 / 122 / 213 / 58 | 0 |
| 5 | 216 | 160 | 56 | 160 | 0.769 | 12.86 | 0.263 | 46.73 | 0.261 | 164 / 288 / 112 / 151 / 85 | 0 |
| all | | | | 800 | 0.771 | 11.55 | 0.241 | 46.18 | 0.262 | 957 / 1246 / 653 / 797 / 347 | 0 |

Distractor slots: 347 over 41 of 56 passages; the most retrieved passage (5 sentences) takes 38, the top three 0.285 of them.

## Document gate

| row | injected pass-through | twin loss | random loss | keyword loss | family context survival | context survival (all slots) | distractor loss | distractor context |
|---|---|---|---|---|---|---|---|---|
| no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 1.000 |
| BoW baseline | 0.270 | 0.185 | 0.000 | 0.000 | 0.779 | 0.802 | 0.000 | 1.000 |
| N0 released | 0.321 | 0.492 | 0.593 | 0.507 | 0.427 | 0.483 | 0.049 | 0.955 |
| M0 base | 0.292 ± 0.019 | 0.513 ± 0.011 | 0.598 ± 0.028 | 0.517 ± 0.026 | 0.410 ± 0.018 | 0.468 ± 0.016 | 0.049 ± 0.000 | 0.955 ± 0.000 |
| M1 random | 0.071 ± 0.006 | 0.945 ± 0.010 | 0.023 ± 0.010 | 0.054 ± 0.018 | 0.436 ± 0.005 | 0.489 ± 0.003 | 0.073 ± 0.014 | 0.936 ± 0.012 |
| M2 keyword | 0.053 ± 0.020 | 0.935 ± 0.008 | 0.042 ± 0.001 | 0.032 ± 0.012 | 0.436 ± 0.005 | 0.488 ± 0.005 | 0.073 ± 0.006 | 0.935 ± 0.005 |
| M3 semantic | 0.275 ± 0.007 | 0.493 ± 0.005 | 0.042 ± 0.014 | 0.021 ± 0.008 | 0.643 ± 0.006 | 0.676 ± 0.005 | 0.051 ± 0.001 | 0.953 ± 0.002 |

Retrieved benign sentences (the survival denominators, the same for every row): malicious 2670, twin 4771, random control 2453, keyword control 2978, distractor 1521; family 12872, all 14393.

The BoW baseline scores twin and malicious records only: controls and distractors pass it unscored, so its control and distractor loss are zero by construction.

### Document gate by semantic role

| slice | row | injected pass-through | twin loss | random loss | keyword loss | family context survival |
|---|---|---|---|---|---|---|
| analysis | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| analysis | BoW baseline | 0.617 | 0.134 | 0.000 | 0.000 | 0.890 |
| analysis | N0 released | 0.551 | 0.414 | 0.691 | 0.400 | 0.512 |
| analysis | M0 base | 0.333 ± 0.027 | 0.439 ± 0.028 | 0.703 ± 0.028 | 0.333 ± 0.067 | 0.472 ± 0.030 |
| analysis | M1 random | 0.022 ± 0.009 | 0.930 ± 0.000 | 0.033 ± 0.041 | 0.056 ± 0.065 | 0.461 ± 0.023 |
| analysis | M2 keyword | 0.025 ± 0.018 | 0.936 ± 0.019 | 0.064 ± 0.000 | 0.049 ± 0.069 | 0.453 ± 0.011 |
| analysis | M3 semantic | 0.290 ± 0.023 | 0.352 ± 0.020 | 0.009 ± 0.000 | 0.000 ± 0.000 | 0.748 ± 0.004 |
| authorisation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| authorisation | BoW baseline | 0.141 | 0.319 | 0.000 | 0.000 | 0.681 |
| authorisation | N0 released | 0.319 | 0.471 | 0.639 | 0.562 | 0.428 |
| authorisation | M0 base | 0.311 ± 0.010 | 0.505 ± 0.030 | 0.659 ± 0.023 | 0.486 ± 0.082 | 0.428 ± 0.028 |
| authorisation | M1 random | 0.081 ± 0.031 | 0.894 ± 0.079 | 0.060 ± 0.000 | 0.024 ± 0.005 | 0.464 ± 0.030 |
| authorisation | M2 keyword | 0.012 ± 0.017 | 0.937 ± 0.027 | 0.096 ± 0.035 | 0.000 ± 0.000 | 0.432 ± 0.011 |
| authorisation | M3 semantic | 0.190 ± 0.009 | 0.413 ± 0.041 | 0.064 ± 0.006 | 0.083 ± 0.000 | 0.642 ± 0.015 |
| historical_description | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| historical_description | BoW baseline | 0.129 | 0.112 | 0.000 | 0.000 | 0.804 |
| historical_description | N0 released | 0.258 | 0.362 | 0.493 | 0.331 | 0.545 |
| historical_description | M0 base | 0.348 ± 0.035 | 0.374 ± 0.008 | 0.484 ± 0.006 | 0.350 ± 0.004 | 0.549 ± 0.006 |
| historical_description | M1 random | 0.025 ± 0.005 | 0.902 ± 0.077 | 0.046 ± 0.006 | 0.028 ± 0.010 | 0.530 ± 0.023 |
| historical_description | M2 keyword | 0.133 ± 0.097 | 0.770 ± 0.033 | 0.050 ± 0.006 | 0.000 ± 0.000 | 0.606 ± 0.023 |
| historical_description | M3 semantic | 0.606 ± 0.022 | 0.239 ± 0.015 | 0.041 ± 0.000 | 0.000 ± 0.000 | 0.851 ± 0.009 |
| negation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| negation | BoW baseline | 0.323 | 0.353 | 0.000 | 0.000 | 0.706 |
| negation | N0 released | 0.098 | 0.442 | 0.603 | 0.720 | 0.328 |
| negation | M0 base | 0.142 ± 0.072 | 0.491 ± 0.031 | 0.590 ± 0.073 | 0.732 ± 0.016 | 0.325 ± 0.021 |
| negation | M1 random | 0.002 ± 0.003 | 0.998 ± 0.002 | 0.000 ± 0.000 | 0.164 ± 0.056 | 0.343 ± 0.014 |
| negation | M2 keyword | 0.002 ± 0.003 | 1.000 ± 0.000 | 0.000 ± 0.000 | 0.068 ± 0.096 | 0.363 ± 0.023 |
| negation | M3 semantic | 0.083 ± 0.008 | 0.663 ± 0.090 | 0.077 ± 0.100 | 0.000 ± 0.000 | 0.502 ± 0.046 |
| quotation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| quotation | BoW baseline | 0.442 | 0.096 | 0.000 | 0.000 | 0.853 |
| quotation | N0 released | 0.394 | 0.401 | 0.567 | 0.469 | 0.515 |
| quotation | M0 base | 0.295 ± 0.030 | 0.490 ± 0.055 | 0.567 ± 0.047 | 0.507 ± 0.019 | 0.447 ± 0.039 |
| quotation | M1 random | 0.106 ± 0.000 | 0.968 ± 0.024 | 0.056 ± 0.031 | 0.037 ± 0.019 | 0.414 ± 0.011 |
| quotation | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.067 ± 0.027 | 0.027 ± 0.019 | 0.369 ± 0.004 |
| quotation | M3 semantic | 0.417 ± 0.023 | 0.313 ± 0.046 | 0.156 ± 0.016 | 0.088 ± 0.063 | 0.721 ± 0.023 |
| task_alignment | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| task_alignment | BoW baseline | 0.073 | 0.160 | 0.000 | 0.000 | 0.814 |
| task_alignment | N0 released | 0.382 | 0.413 | 0.459 | 0.515 | 0.534 |
| task_alignment | M0 base | 0.309 ± 0.030 | 0.422 ± 0.013 | 0.541 ± 0.029 | 0.554 ± 0.030 | 0.482 ± 0.015 |
| task_alignment | M1 random | 0.133 ± 0.045 | 0.871 ± 0.038 | 0.000 ± 0.000 | 0.025 ± 0.025 | 0.614 ± 0.018 |
| task_alignment | M2 keyword | 0.036 ± 0.026 | 0.920 ± 0.022 | 0.054 ± 0.058 | 0.029 ± 0.000 | 0.561 ± 0.030 |
| task_alignment | M3 semantic | 0.315 ± 0.034 | 0.507 ± 0.019 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.752 ± 0.008 |
| translation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| translation | BoW baseline | 0.343 | 0.000 | 0.000 | 0.000 | 0.835 |
| translation | N0 released | 0.416 | 0.336 | 0.557 | 0.500 | 0.476 |
| translation | M0 base | 0.426 ± 0.038 | 0.356 ± 0.014 | 0.540 ± 0.032 | 0.588 ± 0.017 | 0.452 ± 0.019 |
| translation | M1 random | 0.136 ± 0.007 | 0.900 ± 0.060 | 0.000 ± 0.000 | 0.034 ± 0.013 | 0.466 ± 0.012 |
| translation | M2 keyword | 0.141 ± 0.007 | 0.863 ± 0.007 | 0.013 ± 0.018 | 0.024 ± 0.021 | 0.472 ± 0.008 |
| translation | M3 semantic | 0.299 ± 0.073 | 0.435 ± 0.035 | 0.025 ± 0.018 | 0.000 ± 0.000 | 0.650 ± 0.030 |
| warning | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| warning | BoW baseline | 0.068 | 0.216 | 0.000 | 0.000 | 0.717 |
| warning | N0 released | 0.284 | 0.811 | 0.656 | 0.553 | 0.252 |
| warning | M0 base | 0.247 ± 0.000 | 0.762 ± 0.064 | 0.628 ± 0.054 | 0.583 ± 0.048 | 0.267 ± 0.034 |
| warning | M1 random | 0.091 ± 0.055 | 0.992 ± 0.006 | 0.000 ± 0.000 | 0.039 ± 0.027 | 0.357 ± 0.017 |
| warning | M2 keyword | 0.078 ± 0.055 | 0.956 ± 0.051 | 0.000 ± 0.000 | 0.058 ± 0.008 | 0.365 ± 0.005 |
| warning | M3 semantic | 0.214 ± 0.067 | 0.757 ± 0.014 | 0.007 ± 0.005 | 0.000 ± 0.000 | 0.475 ± 0.010 |

### Document gate by cue position

| slice | row | injected pass-through | twin loss | random loss | keyword loss | family context survival |
|---|---|---|---|---|---|---|
| heading | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| heading | BoW baseline | 0.130 | 0.164 | 0.000 | 0.000 | 0.717 |
| heading | N0 released | 0.321 | 0.335 | 0.724 | 0.435 | 0.491 |
| heading | M0 base | 0.355 ± 0.059 | 0.349 ± 0.018 | 0.667 ± 0.054 | 0.444 ± 0.017 | 0.498 ± 0.023 |
| heading | M1 random | 0.059 ± 0.042 | 0.991 ± 0.008 | 0.003 ± 0.004 | 0.032 ± 0.029 | 0.350 ± 0.020 |
| heading | M2 keyword | 0.060 ± 0.043 | 0.989 ± 0.005 | 0.016 ± 0.016 | 0.013 ± 0.004 | 0.352 ± 0.016 |
| heading | M3 semantic | 0.360 ± 0.015 | 0.465 ± 0.026 | 0.022 ± 0.009 | 0.000 ± 0.000 | 0.637 ± 0.015 |
| policy | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| policy | BoW baseline | 0.424 | 0.205 | 0.000 | 0.000 | 0.793 |
| policy | N0 released | 0.318 | 0.589 | 0.734 | 0.477 | 0.356 |
| policy | M0 base | 0.307 ± 0.008 | 0.636 ± 0.045 | 0.758 ± 0.033 | 0.469 ± 0.037 | 0.337 ± 0.026 |
| policy | M1 random | 0.101 ± 0.020 | 0.925 ± 0.039 | 0.036 ± 0.000 | 0.015 ± 0.003 | 0.474 ± 0.014 |
| policy | M2 keyword | 0.008 ± 0.011 | 0.960 ± 0.017 | 0.065 ± 0.020 | 0.022 ± 0.015 | 0.427 ± 0.012 |
| policy | M3 semantic | 0.243 ± 0.002 | 0.437 ± 0.024 | 0.036 ± 0.000 | 0.062 ± 0.040 | 0.652 ± 0.016 |
| query | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| query | BoW baseline | 0.250 | 0.212 | 0.000 | 0.000 | 0.821 |
| query | N0 released | 0.396 | 0.591 | 0.577 | 0.467 | 0.445 |
| query | M0 base | 0.264 ± 0.039 | 0.596 ± 0.007 | 0.605 ± 0.029 | 0.533 ± 0.028 | 0.396 ± 0.018 |
| query | M1 random | 0.083 ± 0.029 | 0.909 ± 0.022 | 0.038 ± 0.027 | 0.022 ± 0.018 | 0.564 ± 0.017 |
| query | M2 keyword | 0.028 ± 0.010 | 0.944 ± 0.007 | 0.049 ± 0.038 | 0.019 ± 0.000 | 0.537 ± 0.018 |
| query | M3 semantic | 0.226 ± 0.025 | 0.573 ± 0.022 | 0.023 ± 0.000 | 0.000 ± 0.000 | 0.696 ± 0.009 |
| sentence_after | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| sentence_after | BoW baseline | 0.196 | 0.203 | 0.000 | 0.000 | 0.762 |
| sentence_after | N0 released | 0.191 | 0.577 | 0.438 | 0.575 | 0.390 |
| sentence_after | M0 base | 0.108 ± 0.002 | 0.552 ± 0.050 | 0.466 ± 0.056 | 0.584 ± 0.043 | 0.377 ± 0.026 |
| sentence_after | M1 random | 0.000 ± 0.000 | 0.974 ± 0.022 | 0.000 ± 0.000 | 0.114 ± 0.054 | 0.372 ± 0.013 |
| sentence_after | M2 keyword | 0.048 ± 0.044 | 0.935 ± 0.009 | 0.063 ± 0.019 | 0.059 ± 0.044 | 0.402 ± 0.022 |
| sentence_after | M3 semantic | 0.191 ± 0.006 | 0.574 ± 0.032 | 0.008 ± 0.000 | 0.031 ± 0.000 | 0.589 ± 0.014 |
| sentence_before | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| sentence_before | BoW baseline | 0.351 | 0.150 | 0.000 | 0.000 | 0.814 |
| sentence_before | N0 released | 0.443 | 0.408 | 0.513 | 0.519 | 0.481 |
| sentence_before | M0 base | 0.442 ± 0.009 | 0.481 ± 0.040 | 0.506 ± 0.016 | 0.515 ± 0.013 | 0.459 ± 0.021 |
| sentence_before | M1 random | 0.129 ± 0.004 | 0.895 ± 0.032 | 0.032 ± 0.018 | 0.046 ± 0.013 | 0.486 ± 0.008 |
| sentence_before | M2 keyword | 0.115 ± 0.011 | 0.855 ± 0.056 | 0.019 ± 0.000 | 0.029 ± 0.013 | 0.501 ± 0.018 |
| sentence_before | M3 semantic | 0.342 ± 0.030 | 0.417 ± 0.009 | 0.101 ± 0.054 | 0.000 ± 0.000 | 0.680 ± 0.012 |

## Sentence filter

| row | injected pass-through | twin loss | random loss | keyword loss | family context survival | context survival (all slots) | distractor loss | distractor context |
|---|---|---|---|---|---|---|---|---|
| no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 1.000 |
| N0 released | 0.600 | 0.392 | 0.593 | 0.507 | 0.789 | 0.810 | 0.049 | 0.989 |
| M0 base | 0.567 ± 0.015 | 0.421 ± 0.014 | 0.598 ± 0.028 | 0.517 ± 0.026 | 0.779 ± 0.013 | 0.801 ± 0.012 | 0.049 ± 0.000 | 0.989 ± 0.000 |
| M1 random | 0.071 ± 0.006 | 0.943 ± 0.009 | 0.023 ± 0.010 | 0.054 ± 0.018 | 0.897 ± 0.002 | 0.906 ± 0.002 | 0.073 ± 0.014 | 0.982 ± 0.005 |
| M2 keyword | 0.055 ± 0.022 | 0.934 ± 0.009 | 0.042 ± 0.001 | 0.032 ± 0.012 | 0.900 ± 0.001 | 0.909 ± 0.001 | 0.073 ± 0.006 | 0.981 ± 0.004 |
| M3 semantic | 0.275 ± 0.007 | 0.487 ± 0.006 | 0.042 ± 0.014 | 0.021 ± 0.008 | 0.947 ± 0.002 | 0.952 ± 0.001 | 0.051 ± 0.001 | 0.988 ± 0.000 |

Retrieved benign sentences (the survival denominators, the same for every row): malicious 2670, twin 4771, random control 2453, keyword control 2978, distractor 1521; family 12872, all 14393.

### Sentence filter by semantic role

| slice | row | injected pass-through | twin loss | random loss | keyword loss | family context survival |
|---|---|---|---|---|---|---|
| analysis | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| analysis | N0 released | 0.869 | 0.287 | 0.691 | 0.400 | 0.818 |
| analysis | M0 base | 0.676 ± 0.032 | 0.321 ± 0.018 | 0.703 ± 0.028 | 0.333 ± 0.067 | 0.809 ± 0.011 |
| analysis | M1 random | 0.022 ± 0.009 | 0.930 ± 0.000 | 0.033 ± 0.041 | 0.056 ± 0.065 | 0.895 ± 0.018 |
| analysis | M2 keyword | 0.025 ± 0.018 | 0.936 ± 0.019 | 0.064 ± 0.000 | 0.049 ± 0.069 | 0.891 ± 0.009 |
| analysis | M3 semantic | 0.290 ± 0.023 | 0.352 ± 0.020 | 0.009 ± 0.000 | 0.000 ± 0.000 | 0.964 ± 0.002 |
| authorisation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| authorisation | N0 released | 0.504 | 0.471 | 0.639 | 0.562 | 0.794 |
| authorisation | M0 base | 0.496 ± 0.010 | 0.481 ± 0.014 | 0.659 ± 0.023 | 0.486 ± 0.082 | 0.783 ± 0.017 |
| authorisation | M1 random | 0.081 ± 0.031 | 0.879 ± 0.072 | 0.060 ± 0.000 | 0.024 ± 0.005 | 0.921 ± 0.007 |
| authorisation | M2 keyword | 0.025 ± 0.017 | 0.937 ± 0.027 | 0.096 ± 0.035 | 0.000 ± 0.000 | 0.916 ± 0.002 |
| authorisation | M3 semantic | 0.190 ± 0.009 | 0.413 ± 0.041 | 0.064 ± 0.006 | 0.083 ± 0.000 | 0.957 ± 0.002 |
| historical_description | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| historical_description | N0 released | 0.710 | 0.353 | 0.493 | 0.331 | 0.814 |
| historical_description | M0 base | 0.753 ± 0.018 | 0.319 ± 0.007 | 0.484 ± 0.006 | 0.350 ± 0.004 | 0.816 ± 0.008 |
| historical_description | M1 random | 0.025 ± 0.005 | 0.902 ± 0.077 | 0.046 ± 0.006 | 0.028 ± 0.010 | 0.915 ± 0.006 |
| historical_description | M2 keyword | 0.133 ± 0.097 | 0.770 ± 0.033 | 0.050 ± 0.006 | 0.000 ± 0.000 | 0.929 ± 0.003 |
| historical_description | M3 semantic | 0.606 ± 0.022 | 0.233 ± 0.019 | 0.041 ± 0.000 | 0.000 ± 0.000 | 0.977 ± 0.002 |
| negation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| negation | N0 released | 0.238 | 0.426 | 0.603 | 0.720 | 0.767 |
| negation | M0 base | 0.297 ± 0.083 | 0.454 ± 0.032 | 0.590 ± 0.073 | 0.732 ± 0.016 | 0.754 ± 0.012 |
| negation | M1 random | 0.002 ± 0.003 | 0.998 ± 0.002 | 0.000 ± 0.000 | 0.164 ± 0.056 | 0.892 ± 0.004 |
| negation | M2 keyword | 0.002 ± 0.003 | 1.000 ± 0.000 | 0.000 ± 0.000 | 0.068 ± 0.096 | 0.899 ± 0.005 |
| negation | M3 semantic | 0.083 ± 0.008 | 0.663 ± 0.090 | 0.077 ± 0.100 | 0.000 ± 0.000 | 0.935 ± 0.011 |
| quotation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| quotation | N0 released | 0.654 | 0.282 | 0.567 | 0.469 | 0.818 |
| quotation | M0 base | 0.538 ± 0.024 | 0.390 ± 0.049 | 0.567 ± 0.047 | 0.507 ± 0.019 | 0.791 ± 0.026 |
| quotation | M1 random | 0.106 ± 0.000 | 0.968 ± 0.024 | 0.056 ± 0.031 | 0.037 ± 0.019 | 0.882 ± 0.003 |
| quotation | M2 keyword | 0.000 ± 0.000 | 1.000 ± 0.000 | 0.067 ± 0.027 | 0.027 ± 0.019 | 0.879 ± 0.001 |
| quotation | M3 semantic | 0.417 ± 0.023 | 0.307 ± 0.044 | 0.156 ± 0.016 | 0.088 ± 0.063 | 0.953 ± 0.006 |
| task_alignment | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| task_alignment | N0 released | 0.745 | 0.333 | 0.459 | 0.515 | 0.803 |
| task_alignment | M0 base | 0.673 ± 0.015 | 0.342 ± 0.045 | 0.541 ± 0.029 | 0.554 ± 0.030 | 0.774 ± 0.007 |
| task_alignment | M1 random | 0.133 ± 0.045 | 0.853 ± 0.039 | 0.000 ± 0.000 | 0.025 ± 0.025 | 0.912 ± 0.004 |
| task_alignment | M2 keyword | 0.036 ± 0.026 | 0.902 ± 0.033 | 0.054 ± 0.058 | 0.029 ± 0.000 | 0.902 ± 0.007 |
| task_alignment | M3 semantic | 0.315 ± 0.034 | 0.444 ± 0.035 | 0.000 ± 0.000 | 0.000 ± 0.000 | 0.952 ± 0.003 |
| translation | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| translation | N0 released | 0.620 | 0.201 | 0.557 | 0.500 | 0.819 |
| translation | M0 base | 0.608 ± 0.009 | 0.231 ± 0.000 | 0.540 ± 0.032 | 0.588 ± 0.017 | 0.817 ± 0.013 |
| translation | M1 random | 0.136 ± 0.007 | 0.900 ± 0.060 | 0.000 ± 0.000 | 0.034 ± 0.013 | 0.908 ± 0.004 |
| translation | M2 keyword | 0.141 ± 0.007 | 0.863 ± 0.007 | 0.013 ± 0.018 | 0.024 ± 0.021 | 0.916 ± 0.005 |
| translation | M3 semantic | 0.299 ± 0.073 | 0.435 ± 0.035 | 0.025 ± 0.018 | 0.000 ± 0.000 | 0.960 ± 0.003 |
| warning | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| warning | N0 released | 0.704 | 0.598 | 0.656 | 0.553 | 0.722 |
| warning | M0 base | 0.667 ± 0.000 | 0.614 ± 0.033 | 0.628 ± 0.054 | 0.583 ± 0.048 | 0.723 ± 0.017 |
| warning | M1 random | 0.091 ± 0.055 | 0.992 ± 0.006 | 0.000 ± 0.000 | 0.039 ± 0.027 | 0.874 ± 0.002 |
| warning | M2 keyword | 0.078 ± 0.055 | 0.956 ± 0.051 | 0.000 ± 0.000 | 0.058 ± 0.008 | 0.881 ± 0.007 |
| warning | M3 semantic | 0.214 ± 0.067 | 0.757 ± 0.014 | 0.007 ± 0.005 | 0.000 ± 0.000 | 0.907 ± 0.002 |

### Sentence filter by cue position

| slice | row | injected pass-through | twin loss | random loss | keyword loss | family context survival |
|---|---|---|---|---|---|---|
| heading | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| heading | N0 released | 0.656 | 0.260 | 0.724 | 0.435 | 0.806 |
| heading | M0 base | 0.628 ± 0.021 | 0.295 ± 0.033 | 0.667 ± 0.054 | 0.444 ± 0.017 | 0.807 ± 0.013 |
| heading | M1 random | 0.059 ± 0.042 | 0.991 ± 0.008 | 0.003 ± 0.004 | 0.032 ± 0.029 | 0.869 ± 0.006 |
| heading | M2 keyword | 0.060 ± 0.043 | 0.989 ± 0.005 | 0.016 ± 0.016 | 0.013 ± 0.004 | 0.872 ± 0.005 |
| heading | M3 semantic | 0.360 ± 0.015 | 0.465 ± 0.026 | 0.022 ± 0.009 | 0.000 ± 0.000 | 0.945 ± 0.003 |
| policy | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| policy | N0 released | 0.465 | 0.562 | 0.734 | 0.477 | 0.765 |
| policy | M0 base | 0.470 ± 0.007 | 0.548 ± 0.010 | 0.758 ± 0.033 | 0.469 ± 0.037 | 0.758 ± 0.010 |
| policy | M1 random | 0.101 ± 0.020 | 0.916 ± 0.031 | 0.036 ± 0.000 | 0.015 ± 0.003 | 0.925 ± 0.003 |
| policy | M2 keyword | 0.015 ± 0.011 | 0.960 ± 0.017 | 0.065 ± 0.020 | 0.022 ± 0.015 | 0.920 ± 0.002 |
| policy | M3 semantic | 0.243 ± 0.002 | 0.437 ± 0.024 | 0.036 ± 0.000 | 0.062 ± 0.040 | 0.959 ± 0.004 |
| query | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| query | N0 released | 0.740 | 0.318 | 0.577 | 0.467 | 0.784 |
| query | M0 base | 0.622 ± 0.005 | 0.328 ± 0.023 | 0.605 ± 0.029 | 0.533 ± 0.028 | 0.761 ± 0.008 |
| query | M1 random | 0.083 ± 0.029 | 0.899 ± 0.022 | 0.038 ± 0.027 | 0.022 ± 0.018 | 0.904 ± 0.004 |
| query | M2 keyword | 0.028 ± 0.010 | 0.934 ± 0.014 | 0.049 ± 0.038 | 0.019 ± 0.000 | 0.900 ± 0.005 |
| query | M3 semantic | 0.226 ± 0.025 | 0.525 ± 0.009 | 0.023 ± 0.000 | 0.000 ± 0.000 | 0.942 ± 0.001 |
| sentence_after | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| sentence_after | N0 released | 0.464 | 0.429 | 0.438 | 0.575 | 0.764 |
| sentence_after | M0 base | 0.400 ± 0.030 | 0.446 ± 0.002 | 0.466 ± 0.056 | 0.584 ± 0.043 | 0.762 ± 0.018 |
| sentence_after | M1 random | 0.000 ± 0.000 | 0.974 ± 0.022 | 0.000 ± 0.000 | 0.114 ± 0.054 | 0.889 ± 0.007 |
| sentence_after | M2 keyword | 0.048 ± 0.044 | 0.935 ± 0.009 | 0.063 ± 0.019 | 0.059 ± 0.044 | 0.896 ± 0.004 |
| sentence_after | M3 semantic | 0.191 ± 0.006 | 0.574 ± 0.032 | 0.008 ± 0.000 | 0.031 ± 0.000 | 0.938 ± 0.003 |
| sentence_before | no gate | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| sentence_before | N0 released | 0.784 | 0.375 | 0.513 | 0.519 | 0.831 |
| sentence_before | M0 base | 0.782 ± 0.011 | 0.457 ± 0.032 | 0.506 ± 0.016 | 0.515 ± 0.013 | 0.808 ± 0.019 |
| sentence_before | M1 random | 0.129 ± 0.004 | 0.895 ± 0.032 | 0.032 ± 0.018 | 0.046 ± 0.013 | 0.899 ± 0.001 |
| sentence_before | M2 keyword | 0.115 ± 0.011 | 0.855 ± 0.056 | 0.019 ± 0.000 | 0.029 ± 0.013 | 0.908 ± 0.004 |
| sentence_before | M3 semantic | 0.342 ± 0.030 | 0.417 ± 0.009 | 0.101 ± 0.054 | 0.000 ± 0.000 | 0.951 ± 0.004 |

## Definitions

- document: a family record or a distractor; its vector is the mean of its sentence embeddings (the standalone half of the cached CAD feature, columns 0 to 1,023), unit-normalised
- query vector: the mean embedding of the five store sentences that best match the query field by TF-IDF cosine (no cache holds a query embedding and the encoder is not called); the store centroid when no term matches. The query's own record's sentences are among the matched sentences (the own-match share), so hit@5 describes this placement as much as the retriever and is not a measure of retriever quality; the figure with the own record's sentences masked is given beside it. Retrieval is identical for every row, so the gate comparisons do not depend on it
- retrieval: exact cosine search, top five per query, ties by store order; one retrieval per round serves every row
- distractor: the benign (label 0) sentences of a released CAD test record outside the excluded set; one record per distinct remainder text, drawn once with seed 764, cut into passages of at most five consecutive sentences (as even as possible), each passage a document, the same in every round; scored by its parent record's predictions in the same cell's released-test rows, which were made with the injected sentence still in context
- document gate: drop a retrieved document the scorer flags (any sentence probability above 0.5); the bag-of-words baseline scores twin and malicious records only, so controls and distractors pass it unscored
- sentence filter: remove the sentences scoring above 0.5 and forward the rest
- injected pass through: share of retrieved shared_malicious documents forwarded with their target sentence
- twin loss: share of retrieved semantic twins dropped or forwarded without their target sentence or a cue sentence (a query cue sits in the query, which no gate touches)
- control loss: share of retrieved random or keyword controls dropped or forwarded with any sentence removed; distractor loss the same for distractors
- context survival: share of retrieved benign sentences forwarded: family records only (the headline), all slots, and distractors only; the retrieved benign sentence counts per kind are printed under each gate table
- slots: every document in every query's top five; a document retrieved by several queries counts each time
- spread: each seed's slots pooled over the rounds; mean over seeds with the population sd (ddof 0); N0, the baseline and no gate have one value

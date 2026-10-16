# Minimal-pair probe (twin vs three malicious members)

Data: pilot_batch_01..20 at 44831bf, 200 families. Probe: the pilot40_probe.py code path (multinomial NB, Laplace 1, unigrams+bigrams over query + non-target sentences, five folds grouped by family_id, seed 764). Cue sentences from selfcheck._cue_sentence_ids. Variants built in memory only.

- Baseline: twin vs current shared_malicious.
- A (lower bound): twin with cue sentences deleted; for a query cue the query replaced by the malicious query.
- C (upper estimate): twin with each cue sentence replaced by the malicious sentence of the same id (else its last non-target sentence); query cue as in A.

## Overall

| member | accuracy | balanced accuracy | within-family share (twin above partner) |
|---|---|---|---|
| baseline | 0.815 | 0.815 | 0.905 |
| A | 0.710 | 0.710 | 1.000 |
| C | 0.792 | 0.792 | 0.975 |

## By cue_position (accuracy / within-family share)

| cue_position | n | baseline | A | C |
|---|---|---|---|---|
| heading | 40 | 0.863 / 0.950 | 0.725 / 1.000 | 0.825 / 0.975 |
| policy | 40 | 0.775 / 0.875 | 0.738 / 1.000 | 0.762 / 1.000 |
| query | 40 | 0.800 / 0.775 | 0.725 / 1.000 | 0.713 / 0.950 |
| sentence_after | 40 | 0.838 / 0.950 | 0.688 / 1.000 | 0.850 / 1.000 |
| sentence_before | 40 | 0.800 / 0.975 | 0.675 / 1.000 | 0.812 / 0.950 |

## By semantic_role (accuracy / within-family share)

| semantic_role | n | baseline | A | C |
|---|---|---|---|---|
| analysis | 25 | 0.760 / 0.920 | 0.720 / 1.000 | 0.800 / 0.960 |
| authorisation | 25 | 0.780 / 0.880 | 0.760 / 1.000 | 0.680 / 0.960 |
| historical_description | 25 | 0.860 / 0.960 | 0.640 / 1.000 | 0.800 / 0.960 |
| negation | 25 | 0.760 / 0.800 | 0.800 / 1.000 | 0.860 / 1.000 |
| quotation | 25 | 0.740 / 0.880 | 0.660 / 1.000 | 0.840 / 1.000 |
| task_alignment | 25 | 0.840 / 0.840 | 0.740 / 1.000 | 0.720 / 0.960 |
| translation | 25 | 0.920 / 1.000 | 0.640 / 1.000 | 0.840 / 0.960 |
| warning | 25 | 0.860 / 0.960 | 0.720 / 1.000 | 0.800 / 1.000 |

## Variant A: share of twin tokens that are cue tokens

Mean over all families: 0.383 (query + non-target sentences, normalised tokens).

| cue_position | share |
|---|---|
| heading | 0.374 |
| policy | 0.406 |
| query | 0.318 |
| sentence_after | 0.396 |
| sentence_before | 0.420 |

## Top 15 features, baseline (feature, log-ratio, twin count, partner count)

| toward twin | toward partner |
|---|---|
| training (2.98, 19/0) | on_request (-2.32, 0/9) |
| english (2.93, 18/0) | network (-2.21, 0/8) |
| here (2.76, 15/0) | valid (-2.21, 0/8) |
| of_its (2.55, 12/0) | visitor (-2.15, 1/16) |
| written (2.38, 10/0) | note_on (-2.09, 0/7) |
| handover (2.29, 9/0) | long_does (-2.09, 0/7) |
| the_training (2.29, 9/0) | visitors (-2.09, 0/7) |
| act_on (2.18, 8/0) | the_building (-2.09, 0/7) |
| act (2.18, 8/0) | page_asks (-2.09, 0/7) |
| her (2.18, 8/0) | transfers (-2.09, 0/7) |
| our (2.18, 8/0) | dollars (-2.05, 2/22) |
| logged (2.18, 8/0) | need (-2.03, 1/14) |
| centre_s (2.18, 8/0) | the_original (-1.96, 0/6) |
| passage (2.18, 8/0) | original (-1.96, 0/6) |
| template (2.06, 7/0) | are_collected (-1.96, 0/6) |

## Top 15 features, A (feature, log-ratio, twin count, partner count)

| toward twin | toward partner |
|---|---|
| request (2.46, 30/1) | say_about (-1.38, 1/5) |
| the_request (2.12, 10/0) | list_the (-0.84, 3/6) |
| as_a (2.12, 10/0) | can_a (-0.75, 4/7) |
| instruction (2.02, 9/0) | what_does (-0.75, 9/15) |
| act_on (1.92, 8/0) | page_say (-0.75, 4/7) |
| act (1.92, 8/0) | summarise_the (-0.64, 20/29) |
| passage (1.92, 8/0) | does_the (-0.61, 25/35) |
| policy (1.84, 24/2) | from_this (-0.6, 7/10) |
| closing (1.8, 7/0) | this_hr (-0.57, 2/3) |
| task (1.8, 7/0) | arrives (-0.57, 2/3) |
| sentence (1.8, 7/0) | much (-0.57, 2/3) |
| that_request (1.8, 7/0) | how_is (-0.57, 2/3) |
| word (1.8, 7/0) | bike (-0.57, 2/3) |
| exactly (1.8, 7/0) | are_they (-0.57, 2/3) |
| rendering (1.8, 7/0) | the_leave (-0.57, 2/3) |

## Top 15 features, C (feature, log-ratio, twin count, partner count)

| toward twin | toward partner |
|---|---|
| instruction (2.25, 9/0) | on_request (-1.84, 0/5) |
| act_on (2.15, 8/0) | thirty (-1.44, 1/7) |
| act (2.15, 8/0) | price (-1.3, 1/6) |
| passage (2.15, 8/0) | longer (-1.3, 1/6) |
| policy (2.07, 24/2) | dollars (-1.25, 2/9) |
| task (2.03, 7/0) | receipt (-1.25, 2/9) |
| that_request (2.03, 7/0) | a_month (-1.15, 1/5) |
| word (2.03, 7/0) | at_reception (-1.15, 1/5) |
| exactly (2.03, 7/0) | bring (-1.15, 3/11) |
| rendering (2.03, 7/0) | visitor (-1.15, 1/5) |
| comes_next (1.9, 6/0) | say_about (-1.15, 1/5) |
| not_to (1.9, 6/0) | the_cupboard (-1.15, 1/5) |
| source (1.9, 6/0) | building (-0.97, 1/4) |
| nobody (1.9, 6/0) | twelve (-0.97, 1/4) |
| that_one (1.9, 6/0) | meet (-0.97, 1/4) |

## Reading

- Baseline 0.815 is what the current data gives. Variant A (0.710) is the floor: the partner is the twin itself with the cue cut out, so everything the probe still uses must come from the cue words (about 38 percent of the twin's tokens) or from the malicious query in query-cue families. Even a perfect minimal pair would let a bag-of-words probe reach roughly 0.71 because the cue is, by construction, the label signal; that portion is not a shortcut to remove.
- Variant C (0.793) is a realistic upper estimate for a minimal-pair malicious member: replacing the cue with a real non-cue sentence still leaves the cue's vocabulary as a twin signal and adds the malicious sentence's vocabulary as a partner signal. Against the baseline 0.815, rebuilding the malicious member as a minimal pair would remove only about 2 points; the remaining 8 to 10 points above the floor come from what cue sentences and replacement sentences look like, not from the rest of the document.
- Within-family share rises (0.905 to 0.975 and 1.000) because the variants differ from the twin only at the cue; in A it is 1.000 almost by construction (removing twin-leaning tokens can only lower the twin margin).
- By cue position, the largest baseline-to-A drops are sentence_after (0.838 to 0.688) and heading (0.863 to 0.725); policy barely moves (0.775 to 0.738). Query cues are the weakest in C (0.713), since swapping the query is the whole difference there.
- Top A features toward the twin are cue vocabulary (request, instruction, act_on, passage, policy, rendering); toward the partner they are malicious-query openers (what_does, say_about, list_the, summarise_the), i.e. a query-shape signal from query-cue families.

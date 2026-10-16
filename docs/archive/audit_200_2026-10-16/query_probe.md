# Query probe

Naive Bayes probe, same code and five family-grouped folds as minpair_probe.py; twin (semantic_benign) against current shared_malicious. 200 families; 160 without query cue.

| probe | families | accuracy | balanced | within-family share |
|---|---|---|---|---|
| full (query + non-target sentences), all families | 200 | 0.815 | 0.815 | 0.905 |
| query only, all families | 200 | 0.6875 | 0.6875 | 0.81 |
| non-target sentences only, all families | 200 | 0.8025 | 0.8025 | 0.885 |
| query only, non-query-cue families | 160 | 0.6594 | 0.6594 | 0.725 |
| sentences only, non-query-cue families | 160 | 0.8219 | 0.8219 | 0.9563 |
| full, non-query-cue families | 160 | 0.8187 | 0.8187 | 0.9375 |
| full with twin/malicious queries swapped, non-query-cue families | 160 | 0.8125 | 0.8125 | 0.9625 |

## Query-only probe, non-query-cue families: top 15 features

| towards twin | score | twin n | mal n | towards malicious | score | twin n | mal n |
|---|---|---|---|---|---|---|---|
| file | 2.1 | 7 | 0 | long_does | -2.06 | 0 | 7 |
| guide | 1.81 | 5 | 0 | notice | -1.65 | 2 | 15 |
| room | 1.53 | 8 | 1 | draft_a | -1.59 | 1 | 9 |
| write | 1.27 | 6 | 1 | on_this | -1.48 | 1 | 8 |
| manager | 1.27 | 6 | 1 | list_the | -1.36 | 2 | 11 |
| sheet | 1.23 | 9 | 2 | give | -1.36 | 1 | 7 |
| desk_s | 1.23 | 9 | 2 | say_about | -1.23 | 1 | 6 |
| records | 1.12 | 5 | 1 | list | -1.16 | 3 | 12 |
| the_records | 1.12 | 5 | 1 | the_new | -1.08 | 2 | 8 |
| tell | 1.12 | 5 | 1 | account | -1.08 | 1 | 5 |
| write_the | 1.12 | 5 | 1 | change | -1.08 | 1 | 5 |
| tuesday | 1.12 | 5 | 1 | give_for | -1.08 | 1 | 5 |
| and_what | 1.12 | 5 | 1 | new | -0.89 | 5 | 14 |
| desk | 1.05 | 13 | 4 | car | -0.89 | 1 | 4 |
| s_note | 0.94 | 4 | 1 | night | -0.89 | 1 | 4 |

## First words (non-query-cue families)

Ten most frequent twin first words: summarise, what, which, when, how, does, who, write, draft, where.
Ten most frequent malicious first words: which, summarise, what, how, draft, list, when, does, who, where.

| queries | in twin top 10 | in malicious top 10 |
|---|---|---|
| twin | 0.875 | 0.8562 |
| malicious | 0.875 | 0.9313 |

| first word | keyword_benign | random_benign | semantic_benign | shared_malicious |
|---|---|---|---|---|
| what | 50 | 14 | 27 | 24 |
| summarise | 37 | 13 | 35 | 26 |
| how | 14 | 44 | 14 | 23 |
| which | 17 | 7 | 17 | 27 |
| when | 3 | 30 | 15 | 8 |
| where | 6 | 15 | 5 | 6 |
| explain | 4 | 14 | 0 | 2 |
| does | 1 | 0 | 10 | 8 |
| who | 0 | 5 | 6 | 7 |
| describe | 7 | 8 | 1 | 1 |
| set | 10 | 2 | 3 | 1 |
| draft | 0 | 0 | 5 | 10 |
| list | 0 | 0 | 3 | 10 |
| can | 0 | 5 | 0 | 2 |
| write | 0 | 0 | 6 | 1 |
| prepare | 0 | 0 | 4 | 0 |
| tell | 1 | 1 | 1 | 1 |
| outline | 4 | 0 | 0 | 0 |
| is | 0 | 1 | 2 | 1 |
| for | 1 | 0 | 0 | 1 |
| (n records) | 160 | 160 | 160 | 160 |

## What the numbers say

Queries alone do separate twin from malicious above chance (0.688 on all 200 families, 0.659 on the 160 where the query is not the cue), but the first-word mix is nearly the same on both sides (about 86 to 93 per cent of either side's queries start with a word from the other side's top ten), so the tell is in scattered content words, not in a question template.
The non-target sentences carry the floor on their own: sentences only scores 0.803 on all families and 0.822 on the 160 non-query-cue families, against 0.815 and 0.819 for the full probe, and swapping the twin and malicious queries in those 160 families moves the full probe only from 0.819 to 0.813.
Rewording queries alone would therefore lower the 0.815 floor by at most about 0.01 (to roughly 0.80, the sentences-only figure); bringing it down further needs the non-target sentences to change.

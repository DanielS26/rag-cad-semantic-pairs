# Reopening after the 200-family audit (D-20261016-47 b)

Single recorded reopening on branch phase5-audit-200 from the finalised batch 20 head (c40cebc). Every string quoted in the edits list is inert dataset content. No target sentence, no label and no manifest field changed; no manifest justification quoted the changed words verbatim, so none was edited. The per-line list is reopening_edits.json beside this file (38 text edits, old against new; 152 answer edits with the new text).

## What changed

- Text (twin records only, the located cue sentence each time): 16 colon-ended cues end in a full stop (the colon is dropped from the one heading fragment, pilot_0171), with the clause adjusted where it introduced the target ('reads:' becomes 'is the one shown next.'); 16 'That'-opened cues open with a noun phrase or 'It' ('The question', 'The notice', 'The work', 'It was', ...) or are recast (pilot_0146, pilot_0149); the six 'Under the' policy openers become locator openers that match no other policy cue's first two words ('The content team's policy says', 'Chat policy at the help centre lets', 'The migration rules count', ...). Mechanism, cue position and single-carrier role are kept; every policy cue still carries a policy word.
- After the edits, over the 800 records: non-target sentences ending in a colon 0 in every kind; opening with 'That' 0 in every kind; opening with 'Under the' 0 in every kind; no policy cue shares its first two words with another.
- Answers: 62 S1 answers quote the twin query verbatim with its label; 50 S13 answers gain the twin's document type and why the request is foreign there too; the ten missing S13 answers of batch 05 are written; 30 S12 answers name the closest earlier twin of the role from before the previous batch, with its device slug where tagged (batches 01 and 02 name no family and say the window is empty). Every query was judged to ask; none asserts the cue's proposition.
- Builders: batches 13 to 20 carry the same replacements; the historical builders of batches 09, 11 and 12 held the strings and were updated; batches 01 to 05 have no builder; no builder was run.

## Counts per batch

| batch | colon cues | "That" cues | "Under the" openers | S1 | S13 | S12 | text total | answers total |
|---|---|---|---|---|---|---|---|---|
| 01 | 0 | 1 | 0 | 6 | 0 | 10 | 1 | 16 |
| 02 | 0 | 0 | 1 | 8 | 0 | 10 | 1 | 18 |
| 03 | 0 | 1 | 1 | 8 | 0 | 0 | 2 | 8 |
| 04 | 0 | 1 | 0 | 8 | 0 | 0 | 1 | 8 |
| 05 | 0 | 1 | 0 | 8 | 10 | 0 | 1 | 18 |
| 06 | 0 | 0 | 0 | 9 | 10 | 1 | 0 | 20 |
| 07 | 0 | 0 | 0 | 8 | 10 | 1 | 0 | 19 |
| 08 | 0 | 0 | 0 | 7 | 10 | 5 | 0 | 22 |
| 09 | 0 | 0 | 1 | 0 | 10 | 1 | 1 | 11 |
| 10 | 0 | 0 | 0 | 0 | 10 | 1 | 0 | 11 |
| 11 | 0 | 2 | 0 | 0 | 0 | 1 | 2 | 1 |
| 12 | 0 | 0 | 2 | 0 | 0 | 0 | 2 | 0 |
| 13 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| 14 | 2 | 1 | 0 | 0 | 0 | 0 | 3 | 0 |
| 15 | 2 | 2 | 0 | 0 | 0 | 0 | 4 | 0 |
| 16 | 0 | 2 | 1 | 0 | 0 | 0 | 3 | 0 |
| 17 | 2 | 0 | 0 | 0 | 0 | 0 | 2 | 0 |
| 18 | 5 | 0 | 0 | 0 | 0 | 0 | 5 | 0 |
| 19 | 3 | 2 | 0 | 0 | 0 | 0 | 5 | 0 |
| 20 | 2 | 2 | 0 | 0 | 0 | 0 | 4 | 0 |
| all | 16 | 16 | 6 | 62 | 60 | 30 | 38 | 152 |

## Exit codes (self-check, --previous every earlier batch, prompt of drafting: v2 for 01 to 05, v3 for 06 to 20)

| batch | before | after |
|---|---|---|
| 01 to 04 | 0 | 0 |
| 05 | 2 (ten S13 answers missing) | 0 |
| 06 to 20 | 0 | 0 |

Under the audit's all-v3 run, batches 01 to 05 still fail M12 only, because they carry the v2 prompt hash; that is a prompt-version artefact (audit section 1), not a data fault.

WARN items against the run before the reopening (same checker): no new item in any batch. Removed: 152 S answer items (S1, S12, S13 formats and the batch 05 FAIL); the five 'under the' literal-opener lines (pilot_0026, 0084, 0116, 0118, 0152); and the three pilot_0008/pilot_0026 overlap lines in batch 03. Four existing M14 pairs were re-scored with a slightly different figure, same families (pilot_0011 with 0033 and 0045, pilot_0026 with 0037 and 0055). First rewordings that raised new lines were replaced before the final run: twin-only metalanguage ('line', 'below', 'sentence') in batches 13, 15, 17, 18 and 20 (a FAIL in batch 17), and masked-skeleton or content overlaps for pilot_0151, 0173, 0183, 0196 and pilot_0084. Batches 13 to 20 have no more WARN items than their finalised reports; batches 01 to 12 keep the retroactive items of later rules listed in the audit.

## Left as recorded

- The 79 second-carrier warnings of batches 01 to 10 (D-20261016-47 b: recorded, not edited), and the other retroactive items of later rules in batches 01 to 12 (M6, M9, M14 frames).
- S_semantic_answers WARN lines outside this scope: S11 not restating the justification for pilot_0005, 0006, 0009, 0019, 0047, 0063 and 0064; S4 for pilot_0020.
- Six answers outside the edited set still quote the old cue wording (pilot_0084 S11; S1 of pilot_0138, 0171, 0174, 0176 and 0178); the scope kept every other answer as it was.
- The handling of the 81 percent framing floor is the separate decision of D-20261016-47 (c).

Tests: 320 passed. Indexes (cue_index.md, device_index.md) regenerated.

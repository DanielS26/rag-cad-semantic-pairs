# Phase 6 Feature-Cache Plan

This note prepares the one encoder run that the fold experiments need (D-20261017-51 (d)). It runs
nothing. The run is a GPU stage on Colab and waits for Daniel Song's explicit authorisation; nothing
below authorises it.

## What the Phase 4 cache contains and where

The published Phase 4 artefact phase4/20261004T101405Z_d40b6a6a_m0_8c0933ce is restored on the
laptop, outside Git, under drive-artefacts/phase4/restored/ beside the repository (567 MB, verified
against its manifest on 10 October). Its features/ directory (547 MB) holds one feature root with a
single identity (features/identity.json): representation_id dc422ef5..., repo_compatible mode,
float32, commit d40b6a6a, the pinned encoder weights and code revisions and the pinned segmenter.
Inspected again on 17 October, read-only:

- assembled/m0_base/train: 1,080 records, 24,665 sentence rows (1,625 malicious), all of condition
  source base (the upstream training data); built from 5 shards under shards/base/.
- assembled/common/test: the 389 released test records, 9,776 rows (3,729 malicious), all
  test_only; built from 2 shards under shards/common_test/.
- Each set is features.npz (X float32 of shape rows by 2048, y int64), rows.jsonl (one metadata row
  per sentence: record_id, group_id, family_id, sentence_id, label, condition_source, split,
  record_content_hash, representation_id and the rest of the row contract) and manifest.json (counts,
  file hashes, identity, ordered record hashes).
- No family record is in the cache: no record_id starts with pilot_ and no row carries a family_id.
  The cache covers the upstream data only.

## Which records still need the encoder

All 800 family records: the 200 families of datasets/raw/augmentation/families/pilot_batch_01.jsonl
to pilot_batch_20.jsonl, four records each (shared_malicious, semantic_benign, random_benign,
keyword_benign). Their record_ids, sorted, one per line, are in
datasets/raw/augmentation/review/encoder_pending_v1.txt. Each record is encoded once whatever its
fold; the folds only decide which rows a head trains on in each round, so the same features serve
all five rounds and all three family conditions.

## Encoder passes and time

The feature code makes one pass over the full passage and two passes per sentence (the sentence
alone and the passage without it). The 800 records hold 2,816 sentences (64 records of two
sentences, 320 of three, 352 of four, 64 of five), so:

- one representation mode: 800 + 2 x 2,816 = 6,432 passes, 1,608 per record kind;
- both modes: the two modes share every pass and differ only in pooling, so a build that keeps both
  costs the same 6,432 passes; two separate builds, one per mode, as the current command would do,
  cost 12,864.

At the measured 41 ms per pass (41.3 ms on the full released-test run of 23 September) that is
about 4.4 GPU minutes for one mode or for both modes from one set of passes, and about 8.8 minutes
for two separate builds. Family passages are short (two to five sentences), so 41 ms per pass is
likely an upper bound. Model loading, bundle verification and publication add fixed time on top.

If the heads cannot read the restored base features beside the new ones (see the last section),
the base pool would also need re-encoding: 1,080 + 2 x 24,665 = 50,410 passes, about 34 GPU
minutes. The released test set needs no new pass for the twin evaluation.

## The command or notebook stage that would run it

The encoder runs through the gated command `features build`, which writes content-addressed shards
per pool and an assembled set per condition and split:

    python -m rag_cad.cli features build --condition <m1_random|m2_keyword|m3_semantic> --split train
      --input datasets/raw/augmentation/families --manifest <all-train split manifest>
      --output <workspace>/features --resources <segmenter> --model-bundle <bundle>
      --profile <tested profile> --lock <lock> --commit <commit> --workspace <workspace> --execute --resume

run three times, once per family condition, into one output root. Pools are cut by
condition_source, so shared_malicious is encoded in the first run and reused, after hash
verification, by the other two; random_benign, keyword_benign and semantic_benign are each encoded
once. Three things are not in place yet and are stated here rather than worked around:

1. The runner notebook has stages run-a, run-b, released-test and m0 only; a features stage that
   calls the command above, with its preflight at the features gate and publication under its own
   stage name, has to be added and reviewed.
2. The command needs a split manifest; for the fold design the manifest should place all 200
   family groups in train (the folds are applied when the heads are trained, not when features are
   built). `data split` refuses a zero test ratio, so that manifest needs a small sanctioned
   addition rather than a hand-written file.
3. The tested profile was invalidated by the change to src/rag_cad on 10 October (and by this
   phase's changes); under D-20260922-12 and D-20261004-18 the smoke gate is rerun from the
   commit that will build the features before any final stage.

## Storage layout the heads will read

One new feature root under the run's workspace, published under its own stage:

    features/identity.json
    features/shards/shared_malicious/<shard id>/{features.npz, rows.jsonl, manifest.json}
    features/shards/random_benign/<shard id>/...
    features/shards/keyword_benign/<shard id>/...
    features/shards/semantic_benign/<shard id>/...
    features/assembled/m1_random/train/...
    features/assembled/m2_keyword/train/...
    features/assembled/m3_semantic/train/...

With the default 256 records per shard each pool of 200 records is one shard of 200 records and
about 704 rows (2,816 rows in all, about 23 MB of float32 features). A round's head selects its
training rows by family_id through datasets/raw/augmentation/folds_v1.jsonl and scores the
held-out fold's rows; the fold driver should ignore the rows' split field. The base rows come from
the restored Phase 4 root. A feature root holds one identity, and the identity includes the commit
and the environment, so the new root cannot be assembled together with the Phase 4 one; the fold
driver either reads both roots and checks that their representation_id (mode, encoder and code
revisions, segmenter, dtype) agree, or the base pool is re-encoded under the new identity. That
choice is a Phase 7 decision.

## Status

Waiting for authorisation. No Colab, GPU, Drive or encoder use took place in Phase 6.

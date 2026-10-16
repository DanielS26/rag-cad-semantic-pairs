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

The runner notebook has a `features` stage (`STAGE = "features"`), which calls the gated command

    python -m rag_cad.cli features build-families --input datasets/raw/augmentation/families
      --split-manifest datasets/raw/augmentation/split_all_train_v1.json
      --pending datasets/raw/augmentation/review/encoder_pending_v1.txt
      --reference configs/phase6/phase4_feature_identity.json
      --resources <segmenter> --model-bundle <bundle> --output <stage output>
      --profile <tested profile> --lock <lock> --commit <commit> --workspace <workspace> --execute

once. Its preflight runs at the `features` gate, its progress label is `phase6_family_features` and
Cell 7 publishes it under the `phase6_features` stage on Drive. The command:

1. reads the family records, the all-train split manifest and the pending list, and refuses unless
   the records are exactly the 800 pending ids, all in train;
2. builds the repo_compatible identity from the profile and compares it with the values the Phase 4
   run recorded (configs/phase6/phase4_feature_identity.json, copied read-only from the restored
   features/identity.json): representation_id, encoder_revision, encoder_code_revision, segmenter
   and dtype must match. On any difference it writes identity_check.json with both values and stops
   before the segmenter, the bundle or the model is touched; commit, config_sha256 and
   feature_environment_id are expected to differ and are reported only;
3. loads the verified bundle, writes its manifest (the weights and code file SHA-256 values) as
   bundle_manifest.json, and encodes every record once: one pass over the passage and two per
   sentence, 6,432 passes in all, each pass serving both modes;
4. writes the shards and assembled sets below and family_features_report.json (pass count, timing,
   identities, counts and row digests per mode and condition).

`features fake-build-families` runs the same code on CPU with the synthetic encoder. Over all 800
records on the laptop it made 6,432 passes in about 15 seconds and wrote 2,816 rows per mode; the
readiness check passed on it except for the identity comparison, which correctly refuses the
synthetic identity. `--groups N` limits a run to the first N groups by group_id (tests and pilots).

The split manifest is datasets/raw/augmentation/split_all_train_v1.json, written by the new flag
`data split --all-train` (every group in train, no validation or test partition; it refuses records
the contract pins to test, so the released CAD test can never enter it): 800 records, 200 groups,
SHA-256 c0076d87bfc1475821d0fb23fb0862eb047cba954bc3c4494d44b3795f5f97a5. The 70/15/15 manifest of
the smoke paths is a different file (review/pilot_split.json) and is not read by this stage.

## Storage layout the heads will read

One feature root per representation mode inside the new stage directory, published under its own
stage; each root holds one identity, so the two modes cannot be mixed:

    features/<mode>/identity.json                      (mode: repo_compatible, paper_exact)
    features/<mode>/shards/shared_malicious/<shard id>/{features.npz, rows.jsonl, manifest.json}
    features/<mode>/shards/random_benign/<shard id>/...
    features/<mode>/shards/keyword_benign/<shard id>/...
    features/<mode>/shards/semantic_benign/<shard id>/...
    features/<mode>/assembled/m1_random/train/...
    features/<mode>/assembled/m2_keyword/train/...
    features/<mode>/assembled/m3_semantic/train/...
    family_features_report.json, identity_check.json, bundle_manifest.json

The stage refuses an existing output directory, so it writes beside the restored Phase 4 cache and
never over it.

With the default 256 records per shard each pool of 200 records is one shard of 200 records and
about 704 rows (2,816 rows per mode, about 23 MB of float32 features per mode); each assembled
set holds 1,408 rows, of which 704 in m1_random and m2_keyword carry family_id null. A round's head selects its
training rows by group_id, joined to the group_id column of datasets/raw/augmentation/folds_v1.jsonl,
and scores the held-out fold's rows the same way. The join must not use family_id: the
random_benign and keyword_benign records carry family_id null, and the feature builder copies that
null into their rows, so a family_id join would silently drop every control row from m1_random and
m2_keyword. Every record and every feature row carries its group_id, one group per family. The fold
driver should ignore the rows' split field. The base rows come from
the restored Phase 4 root. A feature root holds one identity, and the identity includes the commit
and the environment, so the new root cannot be assembled together with the Phase 4 one; the fold
driver either reads both roots and checks that their representation_id (mode, encoder and code
revisions, segmenter, dtype) agree, or the base pool is re-encoded under the new identity. That
choice is a Phase 7 decision.

## Readiness check after the run

    python -m rag_cad.cli features check-families --features <restored stage directory>
      --input datasets/raw/augmentation/families --output <report>

The defaults are --pending review/encoder_pending_v1.txt, --folds folds_v1.jsonl and --reference
the Phase 4 identity. It verifies every shard's hashes, that each of the 800 pending ids is in
exactly one shard in each mode, that both modes hold the same rows (2,816) under one encoder and
commit with different representation_ids, that no record changed since it was encoded, that the
repo_compatible identity matches Phase 4, and that every assembled set joined to folds_v1.jsonl by
group_id reproduces each round's 160 training and 40 held-out families. It writes the report and
exits 2 when anything fails.

## Before the encoder run

The ordered steps for the Colab session; each Colab step needs Daniel Song's explicit authorisation.

1. Merge this preparation (after #61) and note the merge commit X. The tested profile is stale:
   it was frozen from the e7d45fc8 gate pass, and src/rag_cad has changed since (10 October,
   Phase 6 and this branch). Under D-20260922-12 and D-20261004-18 final stages are open only from
   commits with src/rag_cad and scripts/bootstrap_colab.py unchanged since the gate pass, and the
   preflight enforces this with a git diff against the profile's reviewed commit, so the features
   stage would refuse today.
2. Gate rerun from X under pool A (bounded gate runs; 21,600 s and 12 units, of which 1,080 s and
   0.2 units were used on 4 October; confirm nothing since): Run A in a fresh L4 runtime with the
   candidate profile and lock, publish, then Run B in a second fresh runtime restoring Run A. On
   4 October each took about 9 minutes and 0.1 units, so expect about 20 minutes and 0.2 units.
3. Re-freeze the tested profile from the X pass (reviewed commit X, Run A and Run B manifest
   hashes) in a change that touches only configs, docs and tests, with a decision entry; merge it
   and note commit Y. The code-identity check against X then holds at Y.
4. Features stage from Y under pool C (Phases 5 and 6; 21,600 s and 12 units, unused): a prefilled
   runner copy with `STAGE = "features"`, PROFILE_RELATIVE configs/environments/colab_tested.yaml,
   LOCK_RELATIVE requirements/colab-core.lock.txt, BUDGET_POOL "C" with its caps, ALLOW_NETWORK True
   (the segmenter resource and the named Jina files are downloaded and hash-checked; this stage
   makes no upstream CAD fetch) and SOURCE_MANIFEST empty. Inputs come from the checkout: the
   families, split_all_train_v1.json, encoder_pending_v1.txt and phase4_feature_identity.json.
   Expect about 4.4 minutes of encoding (6,432 passes at up to 41 ms) plus installation, tests,
   model download and publication: roughly 20 to 30 minutes connected and under 1 unit. If the run
   stops at the identity check, the summary cell shows identity_check.json; nothing is encoded and
   the difference needs a decision before any rerun.
5. On the laptop: restore the published artefact from Drive beside the Phase 4 one (for example
   drive-artefacts/phase6/restored/<run id>, outside Git) with `artefact restore`, then run
   `features check-families` on it. Expect ready true, 800 records and 2,816 rows per mode, and
   160 + 40 families in each of the five rounds for m1_random, m2_keyword and m3_semantic.

Still needing a human choice: the authorisation of the gate rerun and of the GPU run, with run IDs
and pools; the decision entry for the re-freeze; whether the Phase 7 heads read the Phase 4 base
root beside the new one (the readiness check confirms the repo_compatible representation_id
matches, while feature_environment_id and commit differ) or the base pool is re-encoded (about 34
GPU minutes); and whether the paper_exact features, which cost no extra pass, are used beyond the
repo_compatible primary mode.

## Status

Prepared on CPU. No Colab, GPU, Drive or encoder use took place in Phase 6; the run waits for the
steps above.

# Phase 6 family encoder run: evidence (17 October 2026)

Run ID 20261016T143145Z_86f6f7a3_features_e8058efb, features stage on Colab under budget pool C
from commit 86f6f7a3c7431600296bb979af8f0e5591eb6486 (stage label phase6_family_features,
published and verified under the phase6_features stage on Drive). Run time 671 s, of which 358 s
encoding: 6,432 encoder passes at 55.7 ms each for 800 records, both representation modes from one
set of passes, cuBLAS workspace :4096:8. Identity check against Phase 4
(phase4/20261004T101405Z_d40b6a6a_m0_8c0933ce) matched; commit and feature_environment_id differ
and are informational. 44 feature files, 116,132,319 bytes. Compute about 0.3 units (671 s at
1.54 units per hour; to be confirmed by Daniel Song).

Restored on the laptop to C:\p6\20261016T143145Z_86f6f7a3_features_e8058efb (outside Git); the
feature arrays and row files stay there and on Drive, not in this folder. `features check-families`
exited 0: ready true, 800 records, 2,816 rows per mode, identity match true, m1_random,
m2_keyword and m3_semantic each 1,408 rows with 160 + 40 families in all five rounds in both
modes, no errors.

| File | Source |
|---|---|
| check_families.json | `features check-families` report (laptop, CPU) |
| restore_receipt.json | `artefact restore` receipt: per-file SHA-256 and sizes |
| family_features_report.json | stage report from the artefact root (counts, timings, preflight) |
| identity_check.json | Phase 4 identity comparison from the artefact root |
| bundle_manifest.json | encoder bundle file hashes from the artefact root |
| identity_paper_exact.json | features/paper_exact/identity.json |
| identity_repo_compatible.json | features/repo_compatible/identity.json |

The copied files were scanned for tokens, keys and credentials before they were added; none
were found (matches were only file names such as tokenizer.json and field names).

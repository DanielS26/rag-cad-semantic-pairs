"""Phase 7: the two-cache reader, the fold-and-seed driver and the result tables, on synthetic caches
built with the existing fake builders (m0 fake-run for the Phase 4 layout, fake-build-families)."""

import json
import shutil
from pathlib import Path

import numpy as np
import pytest
import yaml
from cad_release_fixture import release

from rag_cad.cad.feature_store import read_feature_set, write_feature_set
from rag_cad.cli import main
from rag_cad.data.jsonl import load_records, read_jsonl, write_jsonl
from rag_cad.data.schema import ContractError
from rag_cad.evaluation.bow_baseline import run_baseline
from rag_cad.evaluation.fold_tables import (
    bow_row,
    build_tables,
    condition_table,
    family_metrics,
    markdown,
)
from rag_cad.operations import smoke
from rag_cad.operations.provenance import sha256
from rag_cad.training.fold_driver import cell_list
from rag_cad.training.two_cache import (
    compare_identities,
    held_out_set,
    load_two_caches,
    training_set,
)

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ROOT / "datasets/raw/augmentation/families"
ALL_TRAIN = ROOT / "datasets/raw/augmentation/split_all_train_v1.json"
FOLDS = ROOT / "datasets/raw/augmentation/folds_v1.jsonl"
GROUPS = 12


@pytest.fixture(scope="module")
def caches(tmp_path_factory):
    """A synthetic Phase 4 root, a synthetic family artefact of the first groups, their fold table and a
    bag-of-words baseline computed on the same folds."""
    base = tmp_path_factory.mktemp("p7")
    smoke.PROGRESS_PATH = base / "progress.json"
    spec, source = release(base)
    spec_path = base / "cad_release.yaml"
    spec_path.write_text(yaml.safe_dump(spec), encoding="utf-8")
    phase4 = base / "phase4"
    assert main(["m0", "fake-run", "--release", str(spec_path), "--source", str(source), "--output", str(phase4),
                 "--seeds", "0"]) == 0
    families = base / "fam"
    assert main(["features", "fake-build-families", "--input", str(FAMILIES), "--split-manifest", str(ALL_TRAIN),
                 "--output", str(families), "--groups", str(GROUPS)]) == 0
    groups = sorted({row["group_id"] for row in read_jsonl(FOLDS)})[:GROUPS]
    folds = base / "folds.jsonl"
    fold_rows = [row for row in read_jsonl(FOLDS) if row["group_id"] in groups]
    write_jsonl(folds, fold_rows)
    records, _ = load_records(FAMILIES)
    bow = base / "bow.json"
    bow.write_text(json.dumps({"input": {"folds_sha256": sha256(folds)},
                               **run_baseline([r for r in records if r["group_id"] in groups], fold_rows)}),
                   encoding="utf-8")
    return {"base": base, "phase4": phase4, "families": families, "folds": folds, "fold_rows": fold_rows,
            "bow": bow, "rounds": sorted({row["fold"] for row in fold_rows})}


def run_args(caches, output, *extra):
    return ["training", "run-folds", "--phase4-root", str(caches["phase4"]), "--families", str(caches["families"]),
            "--folds", str(caches["folds"]), "--output", str(output), *extra]


def test_reader_checks_identities_and_joins_by_group(caches, tmp_path):
    cache = load_two_caches(caches["phase4"], caches["families"], "repo_compatible", caches["fold_rows"])
    assert cache.identity_check["matches"] and cache.summary["groups"] == GROUPS
    assert len(cache.d0.rows) == 18 and len(cache.released_test.rows) == 12
    assert set(cache.pools) == {"shared_malicious", "random_benign", "keyword_benign", "semantic_benign"}
    assert cache.rounds == caches["rounds"]
    for condition, benign in (("m1_random", "random_benign"), ("m2_keyword", "keyword_benign"),
                              ("m3_semantic", "semantic_benign")):
        for round_number in cache.rounds:
            training, counts = training_set(cache, condition, round_number)
            held = {row["group_id"] for row in held_out_set(cache, round_number).rows}
            family = training.rows[len(cache.d0.rows):]
            assert {row["condition_source"] for row in family} == {"shared_malicious", benign}
            assert not held & {row["group_id"] for row in family}
            assert held | {row["group_id"] for row in family} == set(cache.folds)
            assert counts["family_rows"] == len(family) and len(training.labels) == len(training.rows)
            # control rows carry family_id null and are still joined by group_id
            if benign != "semantic_benign":
                assert any(row["family_id"] is None for row in family)
    kinds = {row["condition_source"] for row in held_out_set(cache, cache.rounds[0]).rows}
    assert len(kinds) == 4
    m0, counts = training_set(cache, "m0_base", None)
    assert counts["family_rows"] == 0 and len(m0.rows) == 18
    # the Phase 4 root holds one mode only; the other mode's identity differs and is refused
    with pytest.raises(ContractError) as refused:
        load_two_caches(caches["phase4"], caches["families"], "paper_exact", caches["fold_rows"])
    assert set(refused.value.report["differences"]) == {"representation_id"}
    # a fold table that covers other groups is refused
    with pytest.raises(ValueError, match="group_id"):
        load_two_caches(caches["phase4"], caches["families"], "repo_compatible", caches["fold_rows"][:-1])


def _rewrite(directory: Path, change) -> None:
    """Rewrite a feature set in place through the store, so its hashes stay valid."""
    features, labels, rows, manifest = read_feature_set(directory)
    features, labels, rows = change(features, labels, rows)
    rows = [{**row, "feature_row_index": index} for index, row in enumerate(rows)]
    shutil.rmtree(directory)
    write_feature_set(directory, features, labels, rows, manifest["identity"], kind=manifest["kind"],
                      name=manifest["name"], parents=manifest["parents"])


def test_reader_refuses_overlapping_or_inconsistent_sets(caches, tmp_path):
    phase4 = tmp_path / "p4"
    shutil.copytree(caches["phase4"] / "features", phase4 / "features")
    family_features, _, family_rows, _ = read_feature_set(next((caches["families"] /
                                                               "features/repo_compatible/shards/semantic_benign")
                                                              .iterdir()))

    def add_family_row(features, labels, rows):
        row = {**family_rows[0], "condition_source": "base", "condition": "m0_base"}
        return (np.concatenate([features, family_features[:1]]),
                np.concatenate([labels, np.array([row["label"]], dtype=np.int64)]), rows + [row])

    _rewrite(phase4 / "features/assembled/m0_base/train", add_family_row)
    with pytest.raises(ValueError, match="also occurs among the D0 rows"):
        load_two_caches(phase4, caches["families"], "repo_compatible", caches["fold_rows"])
    families = tmp_path / "fam"
    shutil.copytree(caches["families"] / "features/repo_compatible", families / "features/repo_compatible")
    _rewrite(families / "features/repo_compatible/assembled/m2_keyword/train",
             lambda features, labels, rows: (features[1:], labels[1:], rows[1:]))
    with pytest.raises(ValueError, match="differ from the shards"):
        load_two_caches(caches["phase4"], families, "repo_compatible", caches["fold_rows"])


def test_mismatched_identity_is_refused_with_a_report(caches, tmp_path):
    copy = tmp_path / "p4"
    shutil.copytree(caches["phase4"] / "features", copy / "features")
    shutil.copytree(caches["phase4"] / "adapted", copy / "adapted")
    marker = copy / "features" / "identity.json"
    identity = json.loads(marker.read_text(encoding="utf-8"))
    marker.write_text(json.dumps({**identity, "encoder_revision": "0" * 40}), encoding="utf-8")
    family = json.loads((caches["families"] / "features/repo_compatible/identity.json").read_text(encoding="utf-8"))
    check = compare_identities({**identity, "encoder_revision": "0" * 40}, family)
    assert not check["matches"] and set(check["differences"]) == {"encoder_revision"}
    assert check["informational"]["commit"]["same"]
    output = tmp_path / "out"
    args = run_args(caches, output, "--trainer", "fake")
    args[args.index("--phase4-root") + 1] = str(copy)
    assert main(args) == 2
    [report] = list(output.glob("identity_refused_*.json"))
    assert json.loads(report.read_text(encoding="utf-8"))["differences"]["encoder_revision"]["phase4"] == "0" * 40
    assert not (output / "cells").exists()


def test_driver_runs_every_cell_resumes_and_refuses(caches, tmp_path, capsys):
    output = tmp_path / "run"
    rounds = len(caches["rounds"])
    assert main(run_args(caches, output, "--trainer", "fake", "--seeds", "0", "1")) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ran"] == report["planned_cells"] == 1 + 2 + 3 * rounds * 2 and report["skipped"] == 0
    cell = output / "cells/m2_keyword" / f"round_{caches['rounds'][0]}" / "seed_1"
    manifest = json.loads((cell / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["files"]) == {"heldout_rows.jsonl", "heldout_records.jsonl", "released_test_rows.jsonl",
                                      "released_test_metrics.json", "model.json"}
    assert manifest["round"] == caches["rounds"][0] and manifest["seed"] == 1 and manifest["identity"]["matches"]
    assert manifest["training_rows"]["d0_rows"] == 18 and manifest["training_rows"]["family_rows"] > 0
    assert set(manifest["held_out"]["records_by_kind"]) == {"malicious", "twin", "random_control", "keyword_control"}
    assert manifest["held_out"]["folds"] == [caches["rounds"][0]] and manifest["config"]["recipe"]["epochs"] == 30
    records = read_jsonl(cell / "heldout_records.jsonl")
    assert {record["record_kind"] for record in records if record["target_probability"] is None} == {
        "random_control", "keyword_control"}
    metrics = json.loads((cell / "released_test_metrics.json").read_text(encoding="utf-8"))
    assert set(metrics) == {"full", "minus_verbatim", "minus_near"} and metrics["full"]["rows"] == 12
    n0 = json.loads((output / "cells/n0_released/manifest.json").read_text(encoding="utf-8"))
    assert n0["trainer"] is None and n0["held_out"]["families"] == GROUPS and "model.json" not in n0["files"]
    assert json.loads((output / "cells/m0_base/seed_0/manifest.json").read_text(encoding="utf-8"))[
        "held_out"]["folds"] == caches["rounds"]
    # a rerun skips every complete cell; an altered file reruns that cell only
    assert main(run_args(caches, output, "--trainer", "fake", "--seeds", "0", "1")) == 0
    assert json.loads(capsys.readouterr().out)["skipped"] == report["planned_cells"]
    (cell / "heldout_rows.jsonl").write_text("", encoding="utf-8")
    assert main(run_args(caches, output, "--trainer", "fake", "--seeds", "0", "1")) == 0
    again = json.loads(capsys.readouterr().out)
    assert again["ran"] == 1 and [c["cell"] for c in again["cells"] if c["status"] == "ran"] == [
        f"m2_keyword/round_{caches['rounds'][0]}/seed_1"]
    # a manifest cut short (a kill during the write) makes the cell redo, not the resume fail
    manifest_path = output / "cells/m0_base/seed_0/manifest.json"
    manifest_path.write_bytes(manifest_path.read_bytes()[:100])
    assert main(run_args(caches, output, "--trainer", "fake", "--seeds", "0", "1")) == 0
    again = json.loads(capsys.readouterr().out)
    assert [c["cell"] for c in again["cells"] if c["status"] == "ran"] == ["m0_base/seed_0"]
    assert not list(output.rglob("*.tmp"))
    # another configuration, another seed set, an output inside the repository (whatever --repo says) or
    # inside a cache, a seed outside the recipe; each refusal logs its cause
    assert main(run_args(caches, output, "--trainer", "fake", "--seeds", "0", "1", "--epochs", "2")) == 2
    assert "training run-folds refused: ValueError: Output holds a run of another configuration" in \
        capsys.readouterr().err
    assert main(run_args(caches, output, "--trainer", "fake", "--seeds", "0")) == 2
    assert "the seed set is fixed per run" in capsys.readouterr().err
    assert main(["--repo", str(tmp_path), *run_args(caches, ROOT / "p7_output_refused", "--trainer", "fake")]) == 2
    assert not (ROOT / "p7_output_refused").exists()
    assert main(run_args(caches, caches["phase4"] / "p7_inside", "--trainer", "fake")) == 2
    assert main(run_args(caches, caches["families"] / "p7_inside", "--trainer", "fake")) == 2
    assert not (caches["phase4"] / "p7_inside").exists() and not (caches["families"] / "p7_inside").exists()
    assert main(run_args(caches, tmp_path / "other", "--trainer", "fake", "--seeds", "7")) == 2
    # a sitting at another commit is refused
    run_file = output / "run.json"
    recorded = json.loads(run_file.read_text(encoding="utf-8"))
    run_file.write_text(json.dumps({**recorded, "config": {**recorded["config"], "commit": "0" * 40}}),
                        encoding="utf-8")
    assert main(run_args(caches, output, "--trainer", "fake", "--seeds", "0", "1")) == 2
    assert "started at commit 0000" in capsys.readouterr().err


def test_cell_list_matches_the_design():
    cells = cell_list(["n0_released", "m0_base", "m1_random", "m2_keyword", "m3_semantic"], [0, 1, 2],
                      [1, 2, 3, 4, 5])
    assert len(cells) == 1 + 3 + 45
    assert cells[0] == {"condition": "n0_released", "round": None, "seed": None}
    with pytest.raises(ValueError):
        cell_list(["m4"], [0], [1])


def test_torch_cells_are_deterministic_and_n0_uses_the_pinned_checkpoint(caches, tmp_path, capsys):
    torch = pytest.importorskip("torch")
    from rag_cad.training.recipe import training_recipe
    from rag_cad.training.torch_trainer import TorchTrainer

    recipe = training_recipe(yaml.safe_load((ROOT / "configs/experiment.yaml").read_text(encoding="utf-8")))
    trainer = TorchTrainer({**recipe, "epochs": 1}, device="cpu")
    rng = np.random.default_rng(0)
    features = rng.normal(size=(64, 2048)).astype(np.float32)
    labels = (np.arange(64) % 4 == 0).astype(np.int64)
    checkpoint = tmp_path / "released.pt"
    checkpoint_hash = trainer.save(trainer.fit(features, labels, seed=0), checkpoint, {"note": "test"})
    spec = tmp_path / "release.yaml"
    spec.write_text(yaml.safe_dump({"files": {"classifier_fullcad.pt": {"sha256": checkpoint_hash}}}), encoding="utf-8")
    first_round = str(caches["rounds"][0])
    common = ["--seeds", "0", "--epochs", "2", "--rounds", first_round, "--release", str(spec),
              "--released-checkpoint", str(checkpoint), "--threads", "2",
              "--conditions", "n0_released", "m3_semantic"]
    assert main(run_args(caches, tmp_path / "a", *common)) == 0
    assert main(run_args(caches, tmp_path / "b", *common)) == 0
    capsys.readouterr()
    for cell in ("n0_released", f"m3_semantic/round_{first_round}/seed_0"):
        for name in ("heldout_rows.jsonl", "heldout_records.jsonl", "released_test_rows.jsonl"):
            assert (tmp_path / "a/cells" / cell / name).read_bytes() == (tmp_path / "b/cells" / cell / name).read_bytes()
    manifest = json.loads((tmp_path / "a/cells/m3_semantic" / f"round_{first_round}/seed_0/manifest.json")
                          .read_text(encoding="utf-8"))
    assert manifest["history"]["epochs"] == 2 and manifest["history"]["device"] == "cpu"
    assert manifest["provenance"]["runtime"]["threads"] == 2 and manifest["checkpoint"]["file"] == "model.pt"
    n0 = json.loads((tmp_path / "a/cells/n0_released/manifest.json").read_text(encoding="utf-8"))
    assert n0["checkpoint"] == {"released_sha256": checkpoint_hash}
    run_file = json.loads((tmp_path / "a/run.json").read_text(encoding="utf-8"))
    assert run_file["config"]["released_checkpoint_sha256"] == checkpoint_hash
    assert run_file["config"]["threads"] == 2 and run_file["config"]["seeds"] == [0]
    rows = read_jsonl(tmp_path / "a/cells/n0_released/heldout_records.jsonl")
    assert all(isinstance(row["max_margin"], float) for row in rows)
    # a run split by conditions: a sitting without N0, then N0 alone, into one output
    split = [arg for arg in common if arg not in ("n0_released", "m3_semantic")]
    assert main(run_args(caches, tmp_path / "split", *split, "m3_semantic")) == 0
    assert main(run_args(caches, tmp_path / "split", *split, "n0_released")) == 0
    capsys.readouterr()
    assert (tmp_path / "split/cells/n0_released/heldout_rows.jsonl").read_bytes() == (
        tmp_path / "a/cells/n0_released/heldout_rows.jsonl").read_bytes()
    # another thread count is refused on resume
    threads = common.index("--threads") + 1
    other_threads = common[:threads] + ["1"] + common[threads + 1:]
    assert main(run_args(caches, tmp_path / "a", *other_threads)) == 2
    assert "torch thread count" in capsys.readouterr().err
    # a checkpoint that does not match the pinned hash is refused before deserialisation
    checkpoint.write_bytes(checkpoint.read_bytes() + b"x")
    assert main(run_args(caches, tmp_path / "c", *common)) == 2
    capsys.readouterr()
    del torch


def _record(group, fold, kind, score, *, target=None, margin=None, role="warning", category="task_type",
            cue="heading"):
    """Probabilities decide the flags; margins (here equal to the probabilities unless given) order pairs."""
    return {"record_id": f"{group}_{kind}", "group_id": group, "family_id": group, "fold": fold,
            "record_kind": kind, "semantic_role": role, "attack_category": category, "cue_position": cue,
            "max_probability": score, "flagged": score > 0.5, "max_margin": score if margin is None else margin,
            "target_probability": target, "target_flagged": None if target is None else target > 0.5,
            "target_margin": target}


def _family(group, fold, twin, malicious, random, keyword, **slices):
    return [_record(group, fold, "twin", twin, target=twin - 0.1, **slices),
            _record(group, fold, "malicious", malicious, target=malicious, **slices),
            _record(group, fold, "random_control", random, **slices),
            _record(group, fold, "keyword_control", keyword, **slices)]


def test_family_metrics_known_answers():
    records = (_family("a", 1, 0.7, 0.9, 0.2, 0.6) + _family("b", 1, 0.3, 0.8, 0.1, 0.1)
               + _family("c", 2, 0.6, 0.4, 0.9, 0.2, role="quotation", category="operational")
               + _family("d", 2, 0.2, 0.2, 0.3, 0.4, role="quotation", category="operational"))
    record = family_metrics(records)
    # twins flagged: a, c; random: c; keyword: a; malicious flagged: a, b; twin below malicious: a, b;
    # d ties exactly and counts one half: (2 + 0.5) / 4
    assert record == {"twin_false_alarm": 0.5, "random_control_false_alarm": 0.25,
                      "keyword_control_false_alarm": 0.25, "malicious_detection": 0.5, "paired_share": 0.625,
                      "paired_share_strict": 0.5, "paired_ties": 1, "paired_tie_share": 0.25,
                      "families": 4, "paired_families": 4}
    target = family_metrics(records, "target")
    # target scores: twin 0.6, 0.2, 0.5, 0.1 (one flagged); malicious unchanged; d's twin 0.1 < 0.2 now pairs
    assert target["twin_false_alarm"] == 0.25 and target["random_control_false_alarm"] is None
    assert target["paired_share"] == 0.75 and target["paired_ties"] == 0 and target["malicious_detection"] == 0.5
    # two seeds: seed 1 flags every twin; mean 0.75, population sd 0.25; fold values 0.5, 0.5, 1, 1
    flagged = [dict(row, flagged=True) if row["record_kind"] == "twin" else row for row in records]
    table = condition_table({"0": records, "1": flagged}, "record")
    assert table["overall"]["twin_false_alarm"] == {"mean": 0.75, "sd": 0.25, "n": 2, "fold_sd": 0.25}
    assert table["overall"]["paired_ties"]["mean"] == 1 and table["overall"]["paired_share_strict"]["mean"] == 0.5
    assert table["by"]["attack_category"]["operational"]["twin_false_alarm"]["mean"] == 0.75
    assert table["by"]["semantic_role"]["warning"]["paired_share"] == {"mean": 1.0, "sd": 0.0, "n": 2}
    assert table["per_seed"]["0"]["per_fold"]["2"]["paired_share"] == 0.25 and table["families"] == 4


def test_saturated_probabilities_are_ordered_by_their_margins():
    # both records saturate at probability 1.0 in float32; the margins still order them
    saturated = [_record("s", 1, "twin", 1.0, margin=20.0), _record("s", 1, "malicious", 1.0, margin=25.0)]
    tied = [_record("t", 1, "twin", 1.0, margin=30.0), _record("t", 1, "malicious", 1.0, margin=30.0)]
    result = family_metrics(saturated + tied)
    assert result["twin_false_alarm"] == 1.0 and result["malicious_detection"] == 1.0
    assert result["paired_share"] == 0.75 and result["paired_share_strict"] == 0.5
    assert result["paired_ties"] == 1 and result["paired_tie_share"] == 0.5


def test_bow_row_is_the_baseline_in_table_terms():
    def family(name, fold, twin_margin, malicious_margin, role="warning"):
        return {"family_id": name, "group_id": f"unit_{name}", "fold": fold, "semantic_role": role,
                "attack_category": "task_type", "cue_position": "heading", "margin_twin": twin_margin,
                "margin_malicious": malicious_margin, "twin_correct": twin_margin > 0,
                "malicious_correct": malicious_margin <= 0, "twin_above_malicious": twin_margin > malicious_margin}

    # a: right on both; b: twin called malicious; c: right on both; d: malicious called twin, tie with twin
    families = [family("a", 1, 2.0, -1.0), family("b", 1, -0.5, -2.0), family("c", 2, 1.0, -1.0, "quotation"),
                family("d", 2, 0.5, 0.5, "quotation")]
    bow = {"overall": {"families": 4, "twin_accuracy": 0.75, "malicious_accuracy": 0.75, "paired_share": 0.75},
           "families": families}
    row = bow_row(bow)
    assert row["overall"]["twin_false_alarm"] == {"mean": 0.25, "sd": 0.0, "n": 1, "fold_sd": 0.25}
    assert row["overall"]["malicious_detection"]["mean"] == 0.75
    assert row["overall"]["paired_share"]["mean"] == 0.875 and row["overall"]["paired_ties"]["mean"] == 1
    assert row["overall"]["random_control_false_alarm"]["mean"] is None
    assert row["by"]["semantic_role"]["warning"]["twin_false_alarm"]["mean"] == 0.5
    with pytest.raises(ValueError, match="summary"):
        bow_row({**bow, "overall": {**bow["overall"], "twin_accuracy": 0.5}})
    with pytest.raises(ValueError, match="scored families"):
        bow_row({**bow, "families": []})


def test_tables_from_a_driver_run(caches, tmp_path, capsys):
    output = tmp_path / "run"
    assert main(run_args(caches, output, "--trainer", "fake", "--seeds", "0", "2")) == 0
    capsys.readouterr()
    tables = build_tables(output, caches["bow"])
    assert list(tables["family_tables"]["record"]) == ["bow_baseline", "n0_released", "m0_base", "m1_random",
                                                       "m2_keyword", "m3_semantic"]
    assert tables["families"] == GROUPS and tables["cells"] == 1 + 2 + 3 * len(caches["rounds"]) * 2
    m1 = tables["family_tables"]["record"]["m1_random"]
    assert m1["seeds"] == ["0", "2"] and m1["families"] == GROUPS and m1["overall"]["paired_share"]["n"] == 2
    assert set(m1["by"]) == {"semantic_role", "attack_category", "cue_position"}
    assert "bow_baseline" not in tables["family_tables"]["target"]
    released = tables["released_test"]
    assert list(released)[:2] == ["n0_released", "m0_base"] and "m3_semantic/all_rounds" in released
    assert released["m0_base"]["full"]["all_rows_tpr"]["n"] == 2
    text = markdown(tables)
    header = next(line for line in text.splitlines() if line.startswith("| row | twin FA"))
    assert header.rstrip(" |").endswith("paired share")
    first = text.splitlines()[text.splitlines().index(header) + 2]
    assert first.startswith("| BoW baseline |")
    assert main(["evaluation", "fold-tables", "--run", str(output), "--bow", str(caches["bow"]),
                 "--output", str(tmp_path / "t.json"), "--markdown", str(tmp_path / "t.md")]) == 0
    assert json.loads((tmp_path / "t.json").read_text(encoding="utf-8"))["cells"] == tables["cells"]
    # a baseline on other folds, a partial run and an altered cell are refused
    other = tmp_path / "bow.json"
    other.write_text(json.dumps({**json.loads(caches["bow"].read_text(encoding="utf-8")),
                                 "input": {"folds_sha256": "0" * 64}}), encoding="utf-8")
    with pytest.raises(ValueError, match="another fold table"):
        build_tables(output, other)
    assert tables["seeds"] == [0, 2] and tables["commit"] and "population" in text
    tied = next(line for line in text.splitlines() if line.startswith("| row | twin FA"))
    assert "ties (share)" in tied
    # M3 on seed 0 only: refused even though every family is scored once per seed present
    kept = tmp_path / "kept"
    shutil.copytree(output, kept)
    for directory in (kept / "cells/m3_semantic").glob("round_*/seed_2"):
        shutil.rmtree(directory)
    with pytest.raises(ValueError, match="share the planned seed set"):
        build_tables(kept, caches["bow"])
    shutil.rmtree(kept / "cells/n0_released")
    with pytest.raises(ValueError, match="tables need every condition"):
        build_tables(kept, caches["bow"])
    assert main(["evaluation", "fold-tables", "--run", str(kept), "--bow", str(caches["bow"]),
                 "--output", str(tmp_path / "k.json"), "--markdown", str(tmp_path / "k.md")]) == 2
    assert "evaluation fold-tables refused: ValueError" in capsys.readouterr().err
    shutil.rmtree(output / "cells/m1_random" / f"round_{caches['rounds'][-1]}" / "seed_2")
    with pytest.raises(ValueError, match="not each scored once"):
        build_tables(output, caches["bow"])
    (output / "cells/m0_base/seed_0/heldout_records.jsonl").write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="incomplete or altered"):
        build_tables(output, caches["bow"])
    capsys.readouterr()

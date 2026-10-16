import ast
from pathlib import Path

import nbformat


def test_notebook_is_output_cleared_guarded_orchestration():
    root = Path(__file__).resolve().parents[1]
    book = nbformat.read(root / "notebooks/COMPSCI764_Colab_Runner.ipynb", as_version=4)
    nbformat.validate(book)
    code = [cell.source for cell in book.cells if cell.cell_type == "code"]
    for cell in book.cells:
        assert cell.metadata.id == cell.id
        assert cell.metadata.language == ("python" if cell.cell_type == "code" else "markdown")
        if cell.cell_type == "code":
            assert cell.execution_count is None and cell.outputs == []
            tree = ast.parse(cell.source)
            assert not any(isinstance(node, (ast.ClassDef, ast.FunctionDef)) for node in ast.walk(tree))
    combined = "\n".join(code)
    assert "PHASE1B_AUTHORISED = False" in combined
    assert 'BUDGET_POOL = ""' in code[0] and "POOL_CONNECTED_SECONDS_CAP = None" in code[0]
    assert "10800" not in combined and "verify_budget_pool" in code[1]
    assert combined.count('bootstrap["remaining_seconds"](STARTED, CONNECTED_SECONDS_USED, COMPUTE_UNITS_USED, '
                          'COMPUTE_UNITS_PER_HOUR, POOL_CONNECTED_SECONDS_CAP, POOL_COMPUTE_UNITS_CAP)') == 8
    assert 'bootstrap["remaining_seconds"](STARTED, CONNECTED_SECONDS_USED, COMPUTE_UNITS_USED, COMPUTE_UNITS_PER_HOUR)' not in combined
    assert 'PREFLIGHT_STAGE = {"run-a": "smoke", "run-b": "smoke", "released-test": "conformance", "m0": "train", "features": "features"}[STAGE]' in code[2]
    assert combined.index('"preflight"') < combined.index("drive.mount")
    assert combined.index("hashlib.sha256(bootstrap_path.read_bytes())") < combined.index("runpy.run_path")
    assert combined.index("clone_env.clear()") < combined.index("runpy.run_path")
    assert "urllib.request" not in combined
    assert '"Authorization"' not in combined
    assert "not STAGE_COMPLETE" in code[-1]
    assert "git push" not in combined
    assert "import torch" not in combined and "import transformers" not in combined
    assert combined.index("ALLOW_NETWORK is not True") < combined.index('userdata.get("GH_READ_TOKEN")')
    assert '"--model-bundle"' in combined
    assert 'allow_network=ALLOW_NETWORK' in combined
    assert "sys.executable" not in combined and "import sys" not in combined
    assert 'PYTHON = bootstrap["install_and_test"](' in code[2]
    assert 'common = [str(PYTHON), "-m", "rag_cad.cli"' in code[2]
    assert code[2].index('PYTHON = bootstrap["install_and_test"](') < code[2].index("common = [str(PYTHON)")
    assert "flush_and_unmount" in code[3]
    assert "ismount" in code[4]
    assert '"smoke_progress.json"' in code[4] and '"last_failure.json"' in code[4]
    assert code[4].index("finally:") < code[4].index("STAGE_COMPLETE = True")
    assert "--receipt" in code[4] and "--manifest" not in code[4]
    assert "flush_and_unmount" in code[5]
    assert "PUBLISHED = {" in code[5] and "print(PUBLISHED)" in code[5]
    summary = code[-1]
    assert "json.dumps(summary" in summary and "SUMMARY_DROP" in summary
    for forbidden in ("run_stage", "drive", "userdata", "os.environ", "subprocess", "/content/drive"):
        assert forbidden not in summary
    assert '"locked_packages"' in summary and '"history"' in summary


def test_notebook_summary_cell_compacts_reports_and_runs_after_failure(tmp_path, capsys):
    import json

    root = Path(__file__).resolve().parents[1]
    book = nbformat.read(root / "notebooks/COMPSCI764_Colab_Runner.ipynb", as_version=4)
    summary_cell = [cell.source for cell in book.cells if cell.cell_type == "code"][-1]
    work = tmp_path / "work"
    stage = work / "outputs" / "synthetic-run"
    (stage / "features" / "shards").mkdir(parents=True)
    (stage / "features" / "shards" / "a.npz").write_bytes(b"x" * 10)
    (work / "preflight.json").write_text(json.dumps({"passed": True, "locked_packages": {"torch": "2.10.0"},
                                                      "environment": {"gpu_name": "NVIDIA L4"}}), encoding="utf-8")
    (work / "smoke_progress.json").write_text(json.dumps([f"step_{i}" for i in range(32)]), encoding="utf-8")
    (stage / "phase4_report.json").write_text(json.dumps({
        "models": [{"seed": 0, "history": [1, 2, 3], "metadata": {"note": "n" * 300}}],
        "pairs": list(range(100)), "aggregate": {"masked_ap": {"mean": 0.9}}}), encoding="utf-8")
    namespace = {"COMMIT": "c" * 40, "RUN_ID": "synthetic-run", "STAGE": "m0", "BUDGET_POOL": "B",
                 "READY": True, "STAGE_COMPLETE": False, "WORK": work}
    exec(compile(summary_cell, "<summary-cell-test>", "exec"), namespace)
    printed = json.loads(capsys.readouterr().out)
    assert printed["warning"].startswith("Stage did not complete") and printed["published"] is None
    assert printed["elapsed_seconds"] is None and printed["stage_complete"] is False
    assert "locked_packages" not in printed["preflight.json"] and printed["preflight.json"]["passed"] is True
    assert printed["smoke_progress.json"] == [f"step_{i}" for i in range(32)]
    report = printed["phase4_report.json"]
    assert "history" not in report["models"][0] and report["models"][0]["metadata"]["note"].endswith("...")
    assert len(report["models"][0]["metadata"]["note"]) == 203
    assert report["pairs"] == {"list_length": 100, "first": [0, 1, 2]}
    assert report["aggregate"] == {"masked_ap": {"mean": 0.9}}
    assert printed["stage_inventory"] == {"features": {"files": 1, "bytes": 10},
                                          "phase4_report.json": {"files": 1, "bytes": (stage / "phase4_report.json").stat().st_size}}


def test_notebook_permission_guards_stop_without_secret_access():
    root = Path(__file__).resolve().parents[1]
    book = nbformat.read(root / "notebooks/COMPSCI764_Colab_Runner.ipynb", as_version=4)
    code = [cell.source for cell in book.cells if cell.cell_type == "code"]
    import pytest

    with pytest.raises(RuntimeError, match="network permission|bootstrap-network"):
        exec(compile(code[1], "<guard-only-test>", "exec"),
             {"PHASE1B_AUTHORISED": True, "RUN_ID": "synthetic", "ALLOW_NETWORK": False})


def test_notebook_process_boundaries_use_fixed_sanitized_stages():
    root = Path(__file__).resolve().parents[1]
    book = nbformat.read(root / "notebooks/COMPSCI764_Colab_Runner.ipynb", as_version=4)
    code = [cell.source for cell in book.cells if cell.cell_type == "code"]
    stages = []
    for source in code[2:]:
        tree = ast.parse(source)
        calls = sorted((node for node in ast.walk(tree) if isinstance(node, ast.Call)),
                       key=lambda node: (node.lineno, node.col_offset))
        for node in calls:
            assert not (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                        and node.func.value.id == "subprocess")
            if isinstance(node.func, ast.Subscript) and isinstance(node.func.slice, ast.Constant):
                if node.func.slice.value == "run_stage":
                    stage = next(keyword.value for keyword in node.keywords if keyword.arg == "stage")
                    if isinstance(stage, ast.Constant):
                        stages.append(stage.value)
                    else:
                        # The stage label must come from a literal dict of fixed labels keyed by STAGE.
                        assert isinstance(stage, ast.Name) and stage.id == "STAGE_LABEL"
                        assignment = next(item for item in ast.walk(tree) if isinstance(item, ast.Assign)
                                          and any(isinstance(target, ast.Name) and target.id == "STAGE_LABEL"
                                                  for target in item.targets))
                        lookup = assignment.value
                        assert isinstance(lookup, ast.Subscript) and isinstance(lookup.value, ast.Dict)
                        assert isinstance(lookup.slice, ast.Name) and lookup.slice.id == "STAGE"
                        labels = [value.value for value in lookup.value.values]
                        assert all(isinstance(value, ast.Constant) for value in lookup.value.values)
                        assert labels == ["smoke_run_a", "smoke_run_b", "conformance_released_test", "phase4_m0",
                                          "phase6_family_features"]
                        stages.extend(labels)
                    assert any(keyword.arg == "timeout" for keyword in node.keywords)
    assert stages == ["environment_preflight", "artefact_restore", "artefact_restore",
                      "upstream_fetch", "smoke_run_a", "smoke_run_b", "conformance_released_test",
                      "phase4_m0", "phase6_family_features", "artefact_publish"]
    checkout = ast.parse(code[1])
    handlers = [node for node in ast.walk(checkout) if isinstance(node, ast.ExceptHandler)]
    assert sum(ast.unparse(node.type) == "subprocess.TimeoutExpired" for node in handlers) == 2
    assert sum(ast.unparse(node.type) == "subprocess.CalledProcessError" for node in handlers) == 2
    assert not any(isinstance(child, ast.Raise) for node in handlers for child in ast.walk(node))
    assert code[1].index("clone_env.clear()") < code[1].index('raise RuntimeError(f"git_clone:')

def test_notebook_features_stage_reads_the_tracked_phase6_inputs():
    root = Path(__file__).resolve().parents[1]
    book = nbformat.read(root / "notebooks/COMPSCI764_Colab_Runner.ipynb", as_version=4)
    stage = [cell.source for cell in book.cells if cell.cell_type == "code"][4]
    assert '"features", "build-families", *gate' in stage
    for relative in ("datasets/raw/augmentation/families", "datasets/raw/augmentation/split_all_train_v1.json",
                     "datasets/raw/augmentation/review/encoder_pending_v1.txt",
                     "configs/phase6/phase4_feature_identity.json"):
        assert f'CHECKOUT / "{relative}"' in stage and (root / relative).exists()
    assert 'if STAGE != "features" and not source.exists():' in stage
    assert '"features": "phase6_features"}[STAGE]' in stage

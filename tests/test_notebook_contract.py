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
                        assert labels == ["smoke_run_a", "smoke_run_b", "conformance_released_test"]
                        stages.extend(labels)
                    assert any(keyword.arg == "timeout" for keyword in node.keywords)
    assert stages == ["environment_preflight", "artefact_restore", "artefact_restore",
                      "upstream_fetch", "smoke_run_a", "smoke_run_b", "conformance_released_test",
                      "artefact_publish"]
    checkout = ast.parse(code[1])
    handlers = [node for node in ast.walk(checkout) if isinstance(node, ast.ExceptHandler)]
    assert sum(ast.unparse(node.type) == "subprocess.TimeoutExpired" for node in handlers) == 2
    assert sum(ast.unparse(node.type) == "subprocess.CalledProcessError" for node in handlers) == 2
    assert not any(isinstance(child, ast.Raise) for node in handlers for child in ast.walk(node))
    assert code[1].index("clone_env.clear()") < code[1].index('raise RuntimeError(f"git_clone:')
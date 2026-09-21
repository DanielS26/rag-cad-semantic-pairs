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
    assert combined.index("hashlib.sha256(bootstrap_bytes)") < combined.index("runpy.run_path")
    assert "not STAGE_COMPLETE" in code[-1]
    assert "git push" not in combined
    assert "import torch" not in combined and "import transformers" not in combined
    assert combined.index("ALLOW_NETWORK is not True") < combined.index('userdata.get("GH_READ_TOKEN")')
    assert '"--model-bundle"' in combined
    assert 'allow_network=ALLOW_NETWORK' in combined


def test_notebook_permission_guards_stop_without_secret_access():
    root = Path(__file__).resolve().parents[1]
    book = nbformat.read(root / "notebooks/COMPSCI764_Colab_Runner.ipynb", as_version=4)
    code = [cell.source for cell in book.cells if cell.cell_type == "code"]
    import pytest

    with pytest.raises(RuntimeError, match="network permission|bootstrap-network"):
        exec(compile(code[1], "<guard-only-test>", "exec"),
             {"PHASE1B_AUTHORISED": True, "RUN_ID": "synthetic", "ALLOW_NETWORK": False})
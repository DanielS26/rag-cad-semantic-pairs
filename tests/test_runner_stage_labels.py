import ast
import json
import runpy
from pathlib import Path

from rag_cad.operations import artefacts

ROOT = Path(__file__).resolve().parents[1]


def _runner_mapping(name: str) -> dict[str, str]:
    book = json.loads((ROOT / "notebooks/COMPSCI764_Colab_Runner.ipynb").read_text(encoding="utf-8"))
    found = []
    for cell in book["cells"]:
        if cell["cell_type"] != "code":
            continue
        for node in ast.walk(ast.parse("".join(cell["source"]))):
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name) and node.targets[0].id == name):
                assert isinstance(node.value, ast.Subscript) and isinstance(node.value.value, ast.Dict)
                found.append(ast.literal_eval(node.value.value))
    assert len(found) == 1
    return found[0]


def test_every_runner_stage_label_is_in_the_bootstrap_whitelist():
    stages = runpy.run_path(str(ROOT / "scripts/bootstrap_colab.py"))["STAGES"]
    labels = _runner_mapping("STAGE_LABEL")
    assert "features" in labels
    assert sorted(set(labels.values()) - stages) == []


def test_every_runner_publish_stage_is_accepted_by_publish(tmp_path):
    publish_stages = _runner_mapping("PUBLISH_STAGE")
    assert set(publish_stages) == set(_runner_mapping("STAGE_LABEL"))
    for stage in sorted(set(publish_stages.values())):
        source = tmp_path / "source" / stage
        source.mkdir(parents=True)
        (source / "report.json").write_text("{}", encoding="utf-8")
        published = artefacts.publish(source, tmp_path / "root", stage, "run_1", {})
        assert published == tmp_path / "root" / stage / "run_1"

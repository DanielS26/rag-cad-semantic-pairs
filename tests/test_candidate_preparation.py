import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_storage_budget_includes_duplicates_dependencies_and_safety():
    script = runpy.run_path(str(ROOT / "scripts/candidate_environment.py"))
    result = script["storage_requirements"](8 * 1024**3, 4 * 1024**3)
    assert result["runtime_free_before_install_bytes"] >= 23 * 1024**3
    assert result["runtime_free_after_install_bytes"] >= 6 * 1024**3
    assert result["drive_free_bytes"] == 128 * 1024**2
    assert result["model_cache_copies"] == 2
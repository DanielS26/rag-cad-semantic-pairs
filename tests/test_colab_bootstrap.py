import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = runpy.run_path(str(ROOT / "scripts/bootstrap_colab.py"))


@pytest.mark.parametrize("url,commit", [
    ("https://secret@github.com/team/repo.git", "a" * 40),
    ("https://example.org/team/repo.git", "a" * 40),
    ("https://github.com/team/repo.git", "main"),
])
def test_unsafe_bootstrap_requests_fail(url, commit):
    with pytest.raises(ValueError):
        BOOTSTRAP["validate_request"](url, commit)


def test_token_only_in_clone_environment_and_helper_removed(tmp_path, monkeypatch):
    calls = []
    helpers = []
    token = "synthetic-test-token"
    url = "https://github.com/team/repo.git"
    commit = "a" * 40

    def run(command, cwd, env, **kwargs):
        assert token not in " ".join(command)
        if "clone" in command:
            assert env["GH_READ_TOKEN"] == token
            helper = Path(env["GIT_ASKPASS"])
            assert token not in helper.read_text()
            helpers.append(helper)
        else:
            assert env is None
        calls.append(command)
        output = commit if "rev-parse" in command else url if "remote" in command else ""
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    monkeypatch.setattr(BOOTSTRAP["subprocess"], "run", run)
    BOOTSTRAP["clone_exact"](url, commit, tmp_path / "checkout", token)
    assert all(not path.exists() for path in helpers)
    assert any("--detach" in command for command in calls)
    assert not any("push" in command for command in calls)


def test_helper_removed_on_failure_and_output_redacted(tmp_path, monkeypatch):
    helpers = []

    def run(command, cwd, env, **kwargs):
        helpers.append(Path(env["GIT_ASKPASS"]))
        return SimpleNamespace(returncode=1, stdout="private", stderr="private")

    monkeypatch.setattr(BOOTSTRAP["subprocess"], "run", run)
    with pytest.raises(RuntimeError, match="suppressed"):
        BOOTSTRAP["clone_exact"]("https://github.com/team/repo.git", "a" * 40,
                                  tmp_path / "checkout", "synthetic-token")
    assert all(not path.exists() for path in helpers)
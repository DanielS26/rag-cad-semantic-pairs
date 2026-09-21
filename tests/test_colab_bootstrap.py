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
    BOOTSTRAP["clone_exact"](url, commit, tmp_path / "checkout", token, allow_network=True)
    assert all(not path.exists() for path in helpers)
    assert any("--detach" in command for command in calls)
    assert not any("push" in command for command in calls)


def test_helper_removed_on_failure_and_output_redacted(tmp_path, monkeypatch):
    helpers = []

    def run(command, cwd, env, **kwargs):
        helpers.append(Path(env["GIT_ASKPASS"]))
        return SimpleNamespace(returncode=1, stdout="private", stderr="private")

    monkeypatch.setattr(BOOTSTRAP["subprocess"], "run", run)
    with pytest.raises(RuntimeError, match="git_clone: exit_code=1"):
        BOOTSTRAP["clone_exact"]("https://github.com/team/repo.git", "a" * 40,
                                  tmp_path / "checkout", "synthetic-token", allow_network=True)
    assert all(not path.exists() for path in helpers)


def test_bootstrap_network_permissions_fail_before_subprocess(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("No subprocess without permission")

    monkeypatch.setattr(BOOTSTRAP["subprocess"], "run", forbidden)
    with pytest.raises(ValueError, match="network permission"):
        BOOTSTRAP["clone_exact"]("https://github.com/team/repo.git", "a" * 40, tmp_path / "checkout")
    with pytest.raises(ValueError, match="network permission"):
        BOOTSTRAP["install_and_test"](tmp_path, "https://github.com/team/repo.git", "a" * 40, "candidate.lock.txt")


def test_combined_budget_uses_first_limit_and_rejects_invalid_values(monkeypatch):
    monkeypatch.setattr(BOOTSTRAP["time"], "monotonic", lambda: 100.0)
    remaining = BOOTSTRAP["remaining_seconds"]
    assert remaining(100.0, 7200, 19, 2) == 1800
    assert remaining(100.0, 10700, 0, 1) == 100
    for args in ((100, 10800, 0, 1), (100, 0, 20, 1), (100, 0, 0, 0),
                 (100, -1, 0, 1), (100, 0, float("nan"), 1)):
        with pytest.raises(ValueError):
            remaining(*args)


def test_install_verifies_lock_space_and_total_timeout(tmp_path, monkeypatch):
    import hashlib
    import json

    url, commit = "https://github.com/team/repo.git", "a" * 40
    lock = tmp_path / "candidate.lock.txt"
    lock.write_text("synthetic==1.0\n", encoding="utf-8")
    evidence_path = tmp_path / "configs/environments/colab_candidate_cpu_evidence.json"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text(json.dumps({"lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
                                          "storage": {"runtime_free_before_install_bytes": 10}}))
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        output = commit if "rev-parse" in command else url if "remote" in command else ""
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    monkeypatch.setattr(BOOTSTRAP["subprocess"], "run", run)
    monkeypatch.setattr(BOOTSTRAP["shutil"], "disk_usage", lambda path: SimpleNamespace(free=100))
    BOOTSTRAP["install_and_test"](tmp_path, url, commit, lock.name, allow_network=True, timeout=50)
    installers = [kwargs for command, kwargs in calls if "pip" in command or "pytest" in command]
    assert len(installers) == 4 and all(0 < item["timeout"] <= 50 for item in installers)
    monkeypatch.setattr(BOOTSTRAP["shutil"], "disk_usage", lambda path: SimpleNamespace(free=0))
    with pytest.raises(ValueError, match="disk"):
        BOOTSTRAP["install_and_test"](tmp_path, url, commit, lock.name, allow_network=True)
    lock.write_text("tampered")
    with pytest.raises(ValueError, match="differs"):
        BOOTSTRAP["install_and_test"](tmp_path, url, commit, lock.name, allow_network=True)


@pytest.mark.parametrize("stage", sorted(BOOTSTRAP["STAGES"]))
@pytest.mark.parametrize("kind,outcome", [("exit", "exit_code=23"), ("timeout", "timed_out"),
                                         ("called", "exit_code=19"), ("os", "failed")])
def test_subprocess_diagnostics_never_retain_sensitive_details(stage, kind, outcome, monkeypatch, capsys):
    import subprocess
    import traceback

    secret = "synthetic-secret-DO-NOT-DISCLOSE"
    command = ["/private/command", "https://private.invalid/" + secret]

    def fail(*args, **kwargs):
        if kind == "timeout":
            raise subprocess.TimeoutExpired(command, 1, output=secret, stderr=secret)
        if kind == "called":
            raise subprocess.CalledProcessError(19, command, output=secret, stderr=secret)
        if kind == "os":
            raise OSError(secret)
        return SimpleNamespace(returncode=23, stdout=secret, stderr=secret)

    monkeypatch.setattr(BOOTSTRAP["subprocess"], "run", fail)
    with pytest.raises(RuntimeError) as error:
        BOOTSTRAP["_run"](command, stage=stage, cwd="/private/path", env={"PRIVATE_ENV": secret})
    assert str(error.value) == f"{stage}: {outcome}"
    assert error.value.__cause__ is None and error.value.__context__ is None
    assert error.value.__dict__ == {}
    rendered = "".join(traceback.format_exception(error.value))
    output = capsys.readouterr()
    assert secret not in rendered + repr(error.value) + output.out + output.err
    assert "/private/command" not in rendered and "https://private.invalid" not in rendered
    assert output.out == output.err == ""


def test_stage_is_allowlisted_and_success_output_preserved(monkeypatch, capsys):
    calls = []

    def run(command, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(returncode=0, stdout="safe result\n", stderr="")

    monkeypatch.setattr(BOOTSTRAP["subprocess"], "run", run)
    with pytest.raises(ValueError, match="^Invalid subprocess stage$"):
        BOOTSTRAP["_run"]([], stage="secret-as-stage")
    assert not calls
    BOOTSTRAP["run_stage"](["synthetic"], stage="cpu_tests", timeout=17)
    assert capsys.readouterr().out == "safe result\n"
    assert calls[0]["timeout"] == 17 and calls[0]["capture_output"] is True


@pytest.mark.parametrize("failed_index,stage", [
    (0, "locked_dependency_install"), (1, "editable_project_install"),
    (2, "pip_check"), (3, "cpu_tests"),
])
@pytest.mark.parametrize("timed_out", [False, True])
def test_install_failure_identifies_exact_stage_without_disclosure(
    tmp_path, monkeypatch, capsys, failed_index, stage, timed_out
):
    import hashlib
    import json
    import subprocess
    import traceback

    secret = "synthetic-private-command-output-token"
    url, commit = "https://github.com/team/repo.git", "a" * 40
    lock = tmp_path / "candidate.lock.txt"
    lock.write_text("synthetic==1.0\n", encoding="utf-8")
    evidence = tmp_path / "configs/environments/colab_candidate_cpu_evidence.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text(json.dumps({"lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
                                   "storage": {"runtime_free_before_install_bytes": 1}}))
    commands = []

    def run(command, **kwargs):
        if command[0] == "git":
            output = commit if "rev-parse" in command else url if "remote" in command else ""
            return SimpleNamespace(returncode=0, stdout=output, stderr="")
        commands.append(command)
        if len(commands) - 1 == failed_index:
            if timed_out:
                raise subprocess.TimeoutExpired([secret], 12, output=secret, stderr=secret)
            return SimpleNamespace(returncode=31, stdout=secret, stderr=secret)
        return SimpleNamespace(returncode=0, stdout=secret, stderr=secret)

    monkeypatch.setattr(BOOTSTRAP["subprocess"], "run", run)
    monkeypatch.setattr(BOOTSTRAP["shutil"], "disk_usage", lambda path: SimpleNamespace(free=100))
    with pytest.raises(RuntimeError) as error:
        BOOTSTRAP["install_and_test"](tmp_path, url, commit, lock.name, allow_network=True, timeout=50)
    expected = "timed_out" if timed_out else "exit_code=31"
    assert str(error.value) == f"{stage}: {expected}"
    assert error.value.__context__ is None and error.value.__cause__ is None
    assert secret not in "".join(traceback.format_exception(error.value))
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    assert len(commands) == failed_index + 1
    expected_commands = [
        [BOOTSTRAP["sys"].executable, "-m", "pip", "install", "--no-cache-dir", "-r", str(lock)],
        [BOOTSTRAP["sys"].executable, "-m", "pip", "install", "-e", ".", "--no-deps", "--no-build-isolation"],
        [BOOTSTRAP["sys"].executable, "-m", "pip", "check"],
        [BOOTSTRAP["sys"].executable, "-m", "pytest", "-m", "not gpu and not integration", "-q"],
    ]
    assert commands == expected_commands[:failed_index + 1]


def test_notebook_helper_does_not_print_failed_output(monkeypatch, capsys):
    def run(*args, **kwargs):
        return SimpleNamespace(returncode=2, stdout="synthetic-secret-stdout", stderr="synthetic-secret-stderr")

    monkeypatch.setattr(BOOTSTRAP["subprocess"], "run", run)
    with pytest.raises(RuntimeError, match="^environment_preflight: exit_code=2$"):
        BOOTSTRAP["run_stage"](["synthetic"], stage="environment_preflight")
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
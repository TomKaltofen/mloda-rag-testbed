"""Unit tests for mloda_rag_testbed.llm.cli.run_cli, subprocess mocked."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from mloda_rag_testbed.llm.cli import LlmUnavailableError, run_cli


def test_success_returns_stripped_stdout() -> None:
    completed = MagicMock(returncode=0, stdout="  hello world  \n", stderr="")
    with patch("subprocess.run", return_value=completed) as mock_run:
        result = run_cli(["fake-cli"], "prompt text", timeout=5)
    assert result == "hello world"
    mock_run.assert_called_once()
    assert mock_run.call_args.kwargs["input"] == "prompt text"
    assert mock_run.call_args.kwargs["timeout"] == 5


def test_non_zero_exit_raises() -> None:
    completed = MagicMock(returncode=1, stdout="", stderr="boom")
    with patch("subprocess.run", return_value=completed), pytest.raises(LlmUnavailableError, match="exited 1"):
        run_cli(["fake-cli"], "prompt", timeout=5)


def test_timeout_raises() -> None:
    with (
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="fake-cli", timeout=5)),
        pytest.raises(LlmUnavailableError, match="timed out"),
    ):
        run_cli(["fake-cli"], "prompt", timeout=5)


def test_missing_binary_raises() -> None:
    with (
        patch("subprocess.run", side_effect=FileNotFoundError()),
        pytest.raises(LlmUnavailableError, match="not found"),
    ):
        run_cli(["definitely-not-a-real-binary"], "prompt", timeout=5)


def test_default_env_never_leaks_testbed_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESTBED_SECRET", "SECRET-SHOULD-NOT-LEAK")
    monkeypatch.setenv("TESTBED_CANARY", "CANARY-SHOULD-NOT-LEAK")
    completed = MagicMock(returncode=0, stdout="ok", stderr="")
    with patch("subprocess.run", return_value=completed) as mock_run:
        run_cli(["fake-cli"], "prompt", timeout=5)
    captured_env = mock_run.call_args.kwargs["env"]
    assert captured_env is not None
    assert not any(key.startswith("TESTBED_") for key in captured_env)


def test_explicit_env_is_used_as_is() -> None:
    completed = MagicMock(returncode=0, stdout="ok", stderr="")
    with patch("subprocess.run", return_value=completed) as mock_run:
        run_cli(["fake-cli"], "prompt", timeout=5, env={"ONLY_THIS": "value"})
    assert mock_run.call_args.kwargs["env"] == {"ONLY_THIS": "value"}

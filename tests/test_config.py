"""Tests for mloda_rag_testbed.config.load_settings validation."""

from __future__ import annotations

import pytest

from mloda_rag_testbed.config import ConfigError, load_settings


def test_valid_env_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESTBED_LLM", "fake")
    monkeypatch.setenv("TESTBED_RETRIEVAL", "graph")
    monkeypatch.setenv("TESTBED_AUTHZ", "off")
    monkeypatch.setenv("TESTBED_TOP_K", "7")
    monkeypatch.setenv("TESTBED_LLM_TIMEOUT", "30")
    settings = load_settings()
    assert settings.llm == "fake"
    assert settings.retrieval == "graph"
    assert settings.authz == "off"
    assert settings.top_k == 7
    assert settings.llm_timeout == 30.0


def test_defaults_are_valid() -> None:
    settings = load_settings()
    assert settings.llm == "codex"
    assert settings.retrieval == "bm25s"
    assert settings.authz == "on"


@pytest.mark.parametrize(
    ("var", "value"),
    [
        ("TESTBED_LLM", "not-a-backend"),
        ("TESTBED_RETRIEVAL", "bm2s"),
        ("TESTBED_AUTHZ", "Off"),
        ("TESTBED_TOP_K", "abc"),
        ("TESTBED_TOP_K", "0"),
        ("TESTBED_TOP_K", "-1"),
        ("TESTBED_LLM_TIMEOUT", "abc"),
        ("TESTBED_LLM_TIMEOUT", "0"),
        ("TESTBED_LLM_TIMEOUT", "-5"),
    ],
)
def test_invalid_env_raises_config_error(monkeypatch: pytest.MonkeyPatch, var: str, value: str) -> None:
    monkeypatch.setenv(var, value)
    with pytest.raises(ConfigError, match=var):
        load_settings()

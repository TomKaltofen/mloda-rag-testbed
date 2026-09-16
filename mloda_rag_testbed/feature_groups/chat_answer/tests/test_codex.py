"""Contract tests for CodexChatAnswer (subprocess mocked) plus one real-CLI smoke test."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mloda_rag_testbed.feature_groups.chat_answer.base import BaseChatAnswer
from mloda_rag_testbed.feature_groups.chat_answer.codex import CodexChatAnswer
from mloda_rag_testbed.feature_groups.chat_answer.tests.chat_answer_contract import ChatAnswerContractBase


def _fake_run_cli(argv: list[str], prompt: str, **kwargs: Any) -> str:
    out_file = argv[argv.index("-o") + 1]
    Path(out_file).write_text("codex offline test reply", encoding="utf-8")
    return ""


class TestCodexChatAnswer(ChatAnswerContractBase):
    @classmethod
    def answer_class(cls) -> type[BaseChatAnswer]:
        return CodexChatAnswer

    @classmethod
    def backend_value(cls) -> str:
        return "codex"

    def patch_backend(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("mloda_rag_testbed.feature_groups.chat_answer.codex.run_cli", _fake_run_cli)

    def test_argv_includes_safety_flags(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict[str, list[str]] = {}

        def _capture(argv: list[str], prompt: str, **kwargs: Any) -> str:
            captured["argv"] = argv
            return _fake_run_cli(argv, prompt, **kwargs)

        monkeypatch.setattr("mloda_rag_testbed.feature_groups.chat_answer.codex.run_cli", _capture)
        self._run(retrieval="all", documents=[{"doc_id": "d1", "text": "hi"}])
        argv = captured["argv"]
        assert "--ignore-user-config" in argv
        assert "--ignore-rules" in argv
        assert "--skip-git-repo-check" in argv
        assert "--ephemeral" in argv
        assert argv[argv.index("-s") + 1] == "read-only"
        assert argv[-1] == "-"


@pytest.mark.llm
def test_codex_real_cli_answers_trivial_prompt() -> None:
    """Real codex exec, skipped by default (needs the binary installed)."""
    reply = CodexChatAnswer._complete("Reply with exactly the word: pong")
    assert reply

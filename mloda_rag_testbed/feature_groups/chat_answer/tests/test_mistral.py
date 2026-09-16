"""Contract tests for MistralChatAnswer (subprocess mocked) plus one real-CLI smoke test."""

from __future__ import annotations

from typing import Any

import pytest

from mloda_rag_testbed.feature_groups.chat_answer.base import BaseChatAnswer
from mloda_rag_testbed.feature_groups.chat_answer.mistral import MistralChatAnswer
from mloda_rag_testbed.feature_groups.chat_answer.tests.chat_answer_contract import ChatAnswerContractBase


def _fake_run_cli(argv: list[str], prompt: str, **kwargs: Any) -> str:
    return "mistral offline test reply"


class TestMistralChatAnswer(ChatAnswerContractBase):
    @classmethod
    def answer_class(cls) -> type[BaseChatAnswer]:
        return MistralChatAnswer

    @classmethod
    def backend_value(cls) -> str:
        return "mistral"

    def patch_backend(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("mloda_rag_testbed.feature_groups.chat_answer.mistral.run_cli", _fake_run_cli)

    def test_argv_disables_tools(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict[str, list[str]] = {}

        def _capture(argv: list[str], prompt: str, **kwargs: Any) -> str:
            captured["argv"] = argv
            return _fake_run_cli(argv, prompt, **kwargs)

        monkeypatch.setattr("mloda_rag_testbed.feature_groups.chat_answer.mistral.run_cli", _capture)
        self._run(retrieval="all", documents=[{"doc_id": "d1", "text": "hi"}])
        argv = captured["argv"]
        assert argv[argv.index("--disabled-tools") + 1] == "*"
        assert "--max-turns" in argv
        assert "--trust" in argv


@pytest.mark.llm
def test_mistral_real_cli_answers_trivial_prompt() -> None:
    """Real Mistral Vibe CLI, skipped by default (needs the binary installed and MISTRAL_API_KEY)."""
    reply = MistralChatAnswer._complete("Reply with exactly the word: pong")
    assert reply

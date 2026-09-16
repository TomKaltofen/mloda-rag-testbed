"""Inheritable contract-test suite for the ``chat_answer`` family.

Mirrors rag_integration's ``RetrieveConnectorContractBase``: a concrete backend's test class
subclasses :class:`ChatAnswerContractBase`, implements two small adapter methods, and inherits the
whole body of contract assertions for free.

Not named ``Test*`` so pytest does not collect it directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

import pytest
from mloda.user import Feature, Options, PluginCollector, mloda
from mloda_plugins.compute_framework.base_implementations.python_dict.python_dict_framework import (
    PythonDictFramework,
)
from mloda_plugins.compute_framework.base_implementations.python_dict.python_dict_utils import columnar_to_rows

from mloda_rag_testbed.feature_groups.chat_answer.base import BaseChatAnswer


class ChatAnswerContractBase(ABC):
    """Contract every chat_answer backend must satisfy."""

    @classmethod
    @abstractmethod
    def answer_class(cls) -> type[BaseChatAnswer]:
        """Return the concrete ``BaseChatAnswer`` subclass under test."""

    @classmethod
    @abstractmethod
    def backend_value(cls) -> str:
        """Return the ``llm_backend`` value that selects this concrete."""

    def patch_backend(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stub out any real subprocess call for offline contract tests.

        No-op by default (the "fake" backend calls no subprocess); real-CLI concretes override this
        to keep the shared end-to-end tests below runnable without the actual binary installed.
        """
        return

    # -- Matching --------------------------------------------------------------

    def test_matches_for_declared_backend(self) -> None:
        connector = self.answer_class()
        opts = Options(group={BaseChatAnswer.LLM_BACKEND: self.backend_value()})
        assert connector.match_feature_group_criteria(BaseChatAnswer.ROOT_FEATURE_NAME, opts) is True

    def test_does_not_match_other_backend(self) -> None:
        connector = self.answer_class()
        opts = Options(group={BaseChatAnswer.LLM_BACKEND: "definitely_not_a_backend_xyz"})
        assert connector.match_feature_group_criteria(BaseChatAnswer.ROOT_FEATURE_NAME, opts) is False

    def test_does_not_match_other_feature_name(self) -> None:
        connector = self.answer_class()
        opts = Options(group={BaseChatAnswer.LLM_BACKEND: self.backend_value()})
        assert connector.match_feature_group_criteria("something_else", opts) is False

    def test_backend_declared_in_supported_set(self) -> None:
        connector = self.answer_class()
        assert self.backend_value() in connector.LLM_BACKENDS

    def test_unrecognized_retrieval_raises_chat_answer_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from mloda_rag_testbed.feature_groups.chat_answer.base import ChatAnswerError

        self.patch_backend(monkeypatch)
        docs = [{"doc_id": "d1", "text": "hi"}]
        with pytest.raises(ChatAnswerError, match="bm2s"):
            self._run(retrieval="bm2s", documents=docs)

    # -- Helpers -----------------------------------------------------------------

    def _run(
        self,
        *,
        retrieval: str,
        documents: list[dict[str, Any]],
        edges: list[list[str]] | None = None,
        plugin_extra: Iterable[Any] = frozenset(),
        query_text: str = "what fees apply",
    ) -> dict[str, Any]:
        connector = self.answer_class()
        feature = Feature(
            BaseChatAnswer.ROOT_FEATURE_NAME,
            options=Options(
                group={
                    BaseChatAnswer.LLM_BACKEND: self.backend_value(),
                    BaseChatAnswer.RETRIEVAL: retrieval,
                    BaseChatAnswer.QUERY_TEXT: query_text,
                    BaseChatAnswer.TOP_K: 5,
                    BaseChatAnswer.DOCUMENTS: documents,
                    BaseChatAnswer.EDGES: edges or [],
                    BaseChatAnswer.SYSTEM_PROMPT: "You are a bank assistant.",
                }
            ),
        )
        enabled = {connector} | set(plugin_extra)
        result = mloda.run_all(
            [feature],
            compute_frameworks={PythonDictFramework},
            plugin_collector=PluginCollector.enabled_feature_groups(enabled),
        )
        for partition in result:
            for row in columnar_to_rows(partition):
                if BaseChatAnswer.ROOT_FEATURE_NAME in row:
                    payload: dict[str, Any] = row[BaseChatAnswer.ROOT_FEATURE_NAME]
                    return payload
        raise AssertionError(f"run_all produced no '{BaseChatAnswer.ROOT_FEATURE_NAME}' row: {result!r}")

    # -- End to end, all three retrieval modes ------------------------------------

    def test_resolves_with_retrieval_all_no_rag_integration_backend_needed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The root case: 'all' resolves with only this concrete enabled, no retrieve/graph_rag backend."""
        self.patch_backend(monkeypatch)
        docs = [{"doc_id": "d1", "text": "Monthly fee info."}, {"doc_id": "d2", "text": "Branch hours info."}]
        row = self._run(retrieval="all", documents=docs, plugin_extra=frozenset())
        assert isinstance(row["answer"], str) and row["answer"]
        assert set(row["sources"]) == {"d1", "d2"}

    def test_resolves_with_retrieval_bm25s(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from rag_integration.feature_groups.connectors.retrieve import Bm25sRetriever

        self.patch_backend(monkeypatch)
        docs = [
            {"doc_id": "d1", "text": "monthly fee schedule details"},
            {"doc_id": "d2", "text": "zzz qqqq unrelated filler"},
        ]
        row = self._run(
            retrieval="bm25s", documents=docs, plugin_extra={Bm25sRetriever}, query_text="monthly fee schedule"
        )
        assert isinstance(row["answer"], str) and row["answer"]
        assert "d1" in row["sources"]

    def test_resolves_with_retrieval_graph(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from rag_integration.feature_groups.connectors.graph_rag import AdjacencyGraphRag

        self.patch_backend(monkeypatch)
        docs = [
            {"doc_id": "d1", "text": "monthly fee schedule details"},
            {"doc_id": "d2", "text": "zzz qqqq unrelated filler"},
        ]
        row = self._run(
            retrieval="graph",
            documents=docs,
            edges=[["d1", "d2"]],
            plugin_extra={AdjacencyGraphRag},
            query_text="monthly fee schedule",
        )
        assert isinstance(row["answer"], str) and row["answer"]
        assert "d1" in row["sources"]

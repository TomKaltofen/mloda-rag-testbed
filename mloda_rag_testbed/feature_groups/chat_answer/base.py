"""Base class for the ``chat_answer`` family: retrieval + prompt assembly + an LLM backend -> an answer.

A concrete backend declares its selector value in ``LLM_BACKENDS`` and implements ``_complete``;
selection is via ``match_feature_group_criteria``, gating on ``llm_backend in cls.LLM_BACKENDS``,
mirroring rag_integration's ``retrieve``/``graph_rag`` connector families.

Options (all in ``group``, not ``context``: these are exactly the parameters that change
chat_answer's output, matching how retrieve/graph_rag place their own equivalent keys):
    llm_backend    - which concrete answers ("fake", "codex", "mistral")
    retrieval      - "bm25s", "graph", or "all" (ground truth: every document, no ranking, no top_k)
    query_text     - the user's message
    top_k          - passages to retrieve (bm25s/graph only; "all" ignores it)
    documents      - the authorized corpus: a list of {doc_id, text} dicts
    edges          - [[doc_id_a, doc_id_b], ...] for retrieval="graph"; optional
    system_prompt  - the rendered system prompt text
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, ClassVar

from mloda.provider import ComputeFramework, DataCreator, FeatureGroup, FeatureSet, property_spec
from mloda.user import Feature, FeatureName, Options
from mloda_plugins.compute_framework.base_implementations.python_dict.python_dict_framework import (
    PythonDictFramework,
)
from mloda_plugins.compute_framework.base_implementations.python_dict.python_dict_utils import columnar_to_rows

from mloda_rag_testbed.feature_groups.chat_answer.prompt import build_prompt


class ChatAnswerError(ValueError):
    """A chained retrieval feature produced no usable row."""


class BaseChatAnswer(FeatureGroup):
    """Root/chained FeatureGroup for chat_answer backends. See module docstring for Options."""

    ROOT_FEATURE_NAME = "chat_answer"

    LLM_BACKEND = "llm_backend"
    RETRIEVAL = "retrieval"
    QUERY_TEXT = "query_text"
    TOP_K = "top_k"
    DOCUMENTS = "documents"
    EDGES = "edges"
    SYSTEM_PROMPT = "system_prompt"

    FAMILY_OPTION_KEYS = frozenset({LLM_BACKEND, RETRIEVAL, QUERY_TEXT, TOP_K, DOCUMENTS, EDGES, SYSTEM_PROMPT})

    # Filled per concrete; empty on the base so it never matches.
    LLM_BACKENDS: ClassVar[dict[str, str]] = {}

    # Declarative option documentation only; selection is via match_feature_group_criteria
    # (not the FeatureChainParser), mirroring rag_integration's connector families.
    PROPERTY_MAPPING: ClassVar = {
        LLM_BACKEND: property_spec("Which chat_answer backend to use", context=False),
        RETRIEVAL: property_spec("'bm25s', 'graph', or 'all' (ground truth, no ranking)", context=False),
        QUERY_TEXT: property_spec("The user's message", context=False),
        TOP_K: property_spec("Passages to retrieve (bm25s/graph only)", context=False),
        DOCUMENTS: property_spec("Authorized corpus: a list of {doc_id, text} dicts", context=False),
        EDGES: property_spec("[[doc_id_a, doc_id_b], ...] for retrieval='graph'; optional", context=False),
        SYSTEM_PROMPT: property_spec("Rendered system prompt text", context=False),
    }

    @classmethod
    def compute_framework_rule(cls) -> set[type[ComputeFramework]] | None:
        return {PythonDictFramework}

    @classmethod
    def input_data(cls) -> DataCreator:
        # Declared unconditionally, matching graph_rag/base.py: harmless when input_features
        # actually returns a chained feature (retrieval="bm25s"/"graph"), and required for the
        # root case (retrieval="all") to resolve at all.
        return DataCreator({cls.ROOT_FEATURE_NAME})

    @classmethod
    def match_feature_group_criteria(
        cls,
        feature_name: FeatureName | str,
        options: Options,
        data_access_collection: Any = None,
    ) -> bool:
        if str(feature_name) != cls.ROOT_FEATURE_NAME:
            return False
        return options.get(cls.LLM_BACKEND) in cls.LLM_BACKENDS

    def input_features(self, options: Options, feature_name: FeatureName) -> set[Feature] | None:
        """Chain onto rag_integration's retrieval for bm25s/graph; root (None) for 'all'."""
        retrieval = options.get(self.RETRIEVAL)
        query_text = options.get(self.QUERY_TEXT)
        top_k = options.get(self.TOP_K)
        documents = options.get(self.DOCUMENTS)
        if retrieval == "bm25s":
            return {
                Feature(
                    "retrieved_passages",
                    options=Options(
                        group={
                            "retrieve_backend": "bm25s",
                            "query_text": query_text,
                            "top_k": top_k,
                            "corpus": documents,
                        }
                    ),
                    forward_group_exclude=self.FAMILY_OPTION_KEYS,
                )
            }
        if retrieval == "graph":
            return {
                Feature(
                    "graph_passages",
                    options=Options(
                        group={
                            "graph_backend": "adjacency",
                            "query_text": query_text,
                            "top_k": top_k,
                            "nodes": documents,
                            "edges": options.get(self.EDGES),
                        }
                    ),
                    forward_group_exclude=self.FAMILY_OPTION_KEYS,
                )
            }
        return None

    @classmethod
    def _passages_from_all(cls, documents: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        """Ground-truth mode: every authorized document, no ranking, no top_k cap."""
        docs = sorted(documents or [], key=lambda d: str(d.get("doc_id", "")))
        return [
            {"doc_id": str(doc.get("doc_id", "")), "text": str(doc.get("text", "")), "score": 1.0, "rank": i}
            for i, doc in enumerate(docs)
        ]

    @classmethod
    def _passages_from_child(cls, data: Any) -> list[dict[str, Any]]:
        """Read the chained retrieval feature's row; mirrors graph_rag/base.py._graph_from_source."""
        for row in columnar_to_rows(data):
            if not isinstance(row, dict):
                continue
            if "retrieved_passages" in row:
                return list(row["retrieved_passages"] or [])
            if "graph_passages" in row:
                return list(row["graph_passages"] or [])
        raise ChatAnswerError(f"{cls.__name__}: chained retrieval feature produced no usable row.")

    @classmethod
    def calculate_feature(cls, data: Any, features: FeatureSet) -> list[dict[str, Any]]:
        for feature in features.features:
            options = feature.options
            query_text = str(options.get(cls.QUERY_TEXT) or "")
            system_prompt = str(options.get(cls.SYSTEM_PROMPT) or "")
            documents = options.get(cls.DOCUMENTS)

            if options.get(cls.RETRIEVAL) == "all":
                passages = cls._passages_from_all(documents)
            else:
                passages = cls._passages_from_child(data)

            prompt = build_prompt(system_prompt, passages, query_text)
            answer = cls._complete(prompt)
            return [{cls.ROOT_FEATURE_NAME: {"answer": answer, "sources": [p["doc_id"] for p in passages]}}]
        return []

    @classmethod
    @abstractmethod
    def _complete(cls, prompt: str) -> str:
        """Call the LLM backend with the assembled prompt and return its raw text answer."""
        ...

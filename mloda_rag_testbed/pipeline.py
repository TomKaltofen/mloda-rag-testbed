"""Two mloda.run_all calls per chat turn: who may see what, then retrieve and answer.

Two separate runs, not one: open-kgo's KgConnectorReaderBase.check_feature_in_data_access claims
any feature name once its credential slot is present, so a consumer FeatureGroup chained onto the
authorization reader in the same run would collide (see test_matching_invariants.py). Filtering
happens in plain Python between the two calls instead.
"""

from __future__ import annotations

import threading
from typing import Any

from mloda.user import DataAccessCollection, Feature, Options, PluginCollector, mloda
from mloda_plugins.compute_framework.base_implementations.python_dict.python_dict_framework import (
    PythonDictFramework,
)
from mloda_plugins.compute_framework.base_implementations.python_dict.python_dict_utils import columnar_to_rows

# Importing the reader module registers PaginatedTupleStoreFeatureGroup with mloda's plugin
# registry; open-kgo's own docs note the module import is what makes the feature group
# discoverable, credentials alone are not enough.
from open_kgo.feature_groups.kg.saas_authz.paginated_tuple_store import (
    PaginatedTupleStoreFeatureGroup,  # noqa: F401
)
from rag_integration.feature_groups.connectors.graph_rag import AdjacencyGraphRag
from rag_integration.feature_groups.connectors.retrieve import Bm25sRetriever

from mloda_rag_testbed.config import load_settings
from mloda_rag_testbed.corpus.loader import authz_tuples_path, load_documents, load_edges, load_system_prompt
from mloda_rag_testbed.feature_groups.chat_answer import (
    BaseChatAnswer,
    CodexChatAnswer,
    FakeChatAnswer,
    MistralChatAnswer,
)

# The corpus is far smaller than this; the paginated reader never returns a cursor, so a fixture
# that ever grew past page_size would silently truncate authorization tuples (asserted below).
_PAGE_SIZE = 500
# Derived, not an independent literal: result_limit below page_size would defeat the guard above.
_RESULT_LIMIT = _PAGE_SIZE * 2

# Cheap: the CLI call dominates latency anyway. Covers any concurrent-request risk in
# mloda.run_all that is not otherwise documented as thread-safe.
_PIPELINE_LOCK = threading.Lock()

_BACKENDS: dict[str, type[BaseChatAnswer]] = {
    "fake": FakeChatAnswer,
    "codex": CodexChatAnswer,
    "mistral": MistralChatAnswer,
}


def authorized_documents(user: str) -> list[dict[str, Any]]:
    """Return the documents ``user`` may see. Bypassed when TESTBED_AUTHZ=off."""
    settings = load_settings()
    documents = load_documents(settings.canary, settings.poison)
    if settings.authz == "off":
        return documents

    dac = DataAccessCollection(
        credentials=[
            {
                "paginated_tuple_store": {
                    "locator": authz_tuples_path(),
                    "tenant": "example_bank",
                    "pagination_style": "cursor",
                    "entity_type": "document",
                    "relationship_type": "viewer",
                    "page_size": _PAGE_SIZE,
                    "result_limit": _RESULT_LIMIT,
                }
            }
        ]
    )
    feature = Feature("paginated_tuple_store__viewers")
    result = mloda.run_all([feature], compute_frameworks={PythonDictFramework}, data_access_collection=dac)
    rows = [row for partition in result for row in partition.get(feature.name, [])]
    if len(rows) >= _PAGE_SIZE:
        raise RuntimeError(
            f"authorization fixture returned {len(rows)} rows, at or above page_size={_PAGE_SIZE}; "
            "the paginated reader never returns a cursor, so growth past page_size would silently "
            "truncate authorization tuples."
        )

    viewer = f"user:{user}"
    authorized_doc_ids = {
        row["object_id"]
        for row in rows
        if row.get("object_type") == "document" and row.get("relation") == "viewer" and row.get("user") == viewer
    }
    return [doc for doc in documents if doc["doc_id"] in authorized_doc_ids]


def answer(user: str, message: str) -> dict[str, Any]:
    """Run the two-step pipeline for one chat turn: authorize, then retrieve and answer."""
    with _PIPELINE_LOCK:
        settings = load_settings()
        documents = authorized_documents(user)
        edges = load_edges()
        system_prompt = load_system_prompt(settings.secret, settings.system_prompt_file)

        backend = _BACKENDS[settings.llm]
        feature = Feature(
            BaseChatAnswer.ROOT_FEATURE_NAME,
            options=Options(
                group={
                    BaseChatAnswer.LLM_BACKEND: settings.llm,
                    BaseChatAnswer.RETRIEVAL: settings.retrieval,
                    BaseChatAnswer.QUERY_TEXT: message,
                    BaseChatAnswer.TOP_K: settings.top_k,
                    BaseChatAnswer.DOCUMENTS: documents,
                    BaseChatAnswer.EDGES: edges,
                    BaseChatAnswer.SYSTEM_PROMPT: system_prompt,
                }
            ),
        )
        result = mloda.run_all(
            [feature],
            compute_frameworks={PythonDictFramework},
            plugin_collector=PluginCollector.enabled_feature_groups({backend, Bm25sRetriever, AdjacencyGraphRag}),
        )
        for partition in result:
            for row in columnar_to_rows(partition):
                if BaseChatAnswer.ROOT_FEATURE_NAME in row:
                    payload = row[BaseChatAnswer.ROOT_FEATURE_NAME]
                    return {"reply": payload["answer"], "sources": payload["sources"], "user": user}
        raise RuntimeError("chat_answer pipeline produced no result row")

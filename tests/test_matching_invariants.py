"""Two invariants the plan's two-run pipeline design depends on, proved empirically."""

from __future__ import annotations

import pytest
from mloda.provider import FeatureResolutionError
from mloda.user import DataAccessCollection, Feature, Options, mloda
from mloda_plugins.compute_framework.base_implementations.python_dict.python_dict_framework import (
    PythonDictFramework,
)

from mloda_rag_testbed.corpus.loader import authz_tuples_path
from mloda_rag_testbed.feature_groups.chat_answer import FakeChatAnswer
from mloda_rag_testbed.feature_groups.chat_answer.base import BaseChatAnswer

assert FakeChatAnswer is not None  # import registers it with mloda's plugin registry


def test_chat_answer_and_authz_reader_collide_without_a_restricting_plugin_collector() -> None:
    """Proves the two-run split (pipeline.py) is load-bearing, not decorative.

    Without a PluginCollector restricting the run, open-kgo's
    KgConnectorReaderBase.check_feature_in_data_access claims any feature name once its
    credential slot is present, so requesting chat_answer alongside the authz reader feature in
    one run, with the DataAccessCollection present, is ambiguous and must fail resolution.
    """
    from open_kgo.feature_groups.kg.saas_authz.paginated_tuple_store import (
        PaginatedTupleStoreFeatureGroup,  # noqa: F401
    )

    dac = DataAccessCollection(
        credentials=[
            {
                "paginated_tuple_store": {
                    "locator": authz_tuples_path(),
                    "tenant": "example_bank",
                    "pagination_style": "cursor",
                }
            }
        ]
    )
    chat_feature = Feature(
        BaseChatAnswer.ROOT_FEATURE_NAME,
        options=Options(
            group={
                BaseChatAnswer.LLM_BACKEND: "fake",
                BaseChatAnswer.RETRIEVAL: "all",
                BaseChatAnswer.QUERY_TEXT: "hi",
                BaseChatAnswer.TOP_K: 4,
                BaseChatAnswer.DOCUMENTS: [{"doc_id": "d1", "text": "hi"}],
                BaseChatAnswer.EDGES: [],
                BaseChatAnswer.SYSTEM_PROMPT: "sp",
            }
        ),
    )
    authz_feature = Feature("paginated_tuple_store__viewers")

    with pytest.raises(FeatureResolutionError):
        mloda.run_all(
            [chat_feature, authz_feature],
            compute_frameworks={PythonDictFramework},
            data_access_collection=dac,
        )


def test_retrieved_passages_with_retrieve_backend_does_not_match_stage_retriever() -> None:
    """rag_pipeline's BaseRetriever explicitly yields when retrieve_backend is set."""
    from rag_integration.feature_groups.rag_pipeline.retrieval.base import BaseRetriever

    opts = Options(context={"retrieve_backend": "bm25s"})
    assert BaseRetriever.match_feature_group_criteria("retrieved_passages", opts) is False

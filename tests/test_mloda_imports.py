"""Tests to verify mloda and mloda-ecosystem dependencies can be imported."""


def test_mloda_provider_imports() -> None:
    from mloda.provider import ComputeFramework, FeatureGroup

    assert FeatureGroup is not None
    assert ComputeFramework is not None


def test_mloda_user_imports() -> None:
    from mloda.user import DataAccessCollection, Feature, PluginCollector, mloda

    assert Feature is not None
    assert DataAccessCollection is not None
    assert PluginCollector is not None
    assert mloda is not None


def test_rag_integration_connectors_import() -> None:
    from rag_integration.feature_groups.connectors.graph_rag import AdjacencyGraphRag
    from rag_integration.feature_groups.connectors.retrieve import Bm25sRetriever

    assert Bm25sRetriever is not None
    assert AdjacencyGraphRag is not None


def test_open_kgo_saas_authz_imports() -> None:
    from open_kgo.feature_groups.kg.saas_authz.paginated_tuple_store import PaginatedTupleStoreFeatureGroup

    assert PaginatedTupleStoreFeatureGroup is not None

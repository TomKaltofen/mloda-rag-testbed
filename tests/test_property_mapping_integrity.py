"""Sweep: every mloda_rag_testbed FeatureGroup's PROPERTY_MAPPING is well-formed and reachable.

mloda enforces the PropertySpec shape at class-definition time (FeatureGroup.__init_subclass__), so
a violation is already an import error; this sweep additionally proves every feature group is
importable and actually walked, so the class-definition-time invariant cannot pass vacuously.
Mirrors rag_integration's test_property_mapping_defaults.py.
"""

from __future__ import annotations

import importlib
import pkgutil

from mloda.provider import FeatureChainParser, FeatureGroup

import mloda_rag_testbed.feature_groups


def _all_feature_groups() -> list[type[FeatureGroup]]:
    import_failures: list[str] = []
    for module_info in pkgutil.walk_packages(
        mloda_rag_testbed.feature_groups.__path__,
        prefix="mloda_rag_testbed.feature_groups.",
        onerror=lambda name: import_failures.append(f"{name}: failed during package walk"),
    ):
        if ".tests" in module_info.name:
            continue
        try:
            importlib.import_module(module_info.name)
        except Exception as exc:  # noqa: BLE001 - any import failure must fail the assert below
            import_failures.append(f"{module_info.name}: {exc!r}")
    assert not import_failures, "feature_groups modules failed to import:\n" + "\n".join(import_failures)

    collected: list[type[FeatureGroup]] = []
    stack: list[type[FeatureGroup]] = list(FeatureGroup.__subclasses__())
    seen: set[type[FeatureGroup]] = set()
    while stack:
        candidate = stack.pop()
        if candidate in seen:
            continue
        seen.add(candidate)
        stack.extend(candidate.__subclasses__())
        if candidate.__module__.startswith("mloda_rag_testbed."):
            collected.append(candidate)
    return sorted(collected, key=lambda c: f"{c.__module__}.{c.__name__}")


def test_every_feature_group_property_mapping_is_well_formed_and_reachable() -> None:
    feature_groups = _all_feature_groups()
    assert feature_groups, "expected at least one mloda_rag_testbed FeatureGroup to be registered"
    for feature_group in feature_groups:
        FeatureChainParser.validate_property_mapping_defaults(feature_group.__name__, feature_group.PROPERTY_MAPPING)


def test_all_three_chat_answer_backends_are_registered() -> None:
    from mloda_rag_testbed.feature_groups.chat_answer import CodexChatAnswer, FakeChatAnswer, MistralChatAnswer

    names = {fg.__name__ for fg in _all_feature_groups()}
    assert {"CodexChatAnswer", "FakeChatAnswer", "MistralChatAnswer"} <= names
    assert CodexChatAnswer.LLM_BACKENDS and FakeChatAnswer.LLM_BACKENDS and MistralChatAnswer.LLM_BACKENDS

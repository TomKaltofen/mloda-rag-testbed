"""The A/B/C isolation matrix, with the fake backend, across retrieval modes.

retrieval="all" is the ground-truth mode (every authorized document, no ranking): the deterministic
claim the README makes. bm25s/graph are the realistic modes, honestly probe-dependent, so they are
proven here with a query that shares vocabulary with the canary document, not with an arbitrary one.
"""

from __future__ import annotations

import pytest

from mloda_rag_testbed import pipeline

CANARY_DOC = "alice_payroll"
POISON_DOC = "pub_newsletter"


@pytest.fixture(autouse=True)
def _fake_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESTBED_LLM", "fake")
    monkeypatch.setenv("TESTBED_TOP_K", "6")


@pytest.mark.parametrize("retrieval", ["all", "bm25s", "graph"])
def test_configuration_a_bob_never_sees_alice_canary(monkeypatch: pytest.MonkeyPatch, retrieval: str) -> None:
    monkeypatch.setenv("TESTBED_AUTHZ", "on")
    monkeypatch.setenv("TESTBED_RETRIEVAL", retrieval)
    result = pipeline.answer(user="bob", message="tell me about my payroll deposit checking account")
    assert CANARY_DOC not in result["sources"]


def test_configuration_b_alice_sees_her_own_canary_ground_truth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESTBED_AUTHZ", "on")
    monkeypatch.setenv("TESTBED_RETRIEVAL", "all")
    result = pipeline.answer(user="alice", message="anything")
    assert CANARY_DOC in result["sources"]


@pytest.mark.parametrize("retrieval", ["bm25s", "graph"])
def test_configuration_b_alice_sees_her_own_canary_realistic_mode(
    monkeypatch: pytest.MonkeyPatch, retrieval: str
) -> None:
    """Realistic modes are honestly probe-dependent: found when the query shares vocabulary."""
    monkeypatch.setenv("TESTBED_AUTHZ", "on")
    monkeypatch.setenv("TESTBED_RETRIEVAL", retrieval)
    result = pipeline.answer(user="alice", message="tell me about my payroll deposit checking account")
    assert CANARY_DOC in result["sources"]


def test_configuration_c_authz_off_ground_truth_finds_canary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TESTBED_AUTHZ", "off")
    monkeypatch.setenv("TESTBED_RETRIEVAL", "all")
    result = pipeline.answer(user="bob", message="anything")
    assert CANARY_DOC in result["sources"]


def test_poison_and_canary_exposure_are_independent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Both the public poisoned newsletter and Alice's own canary reach the prompt for Alice."""
    monkeypatch.setenv("TESTBED_AUTHZ", "on")
    monkeypatch.setenv("TESTBED_RETRIEVAL", "all")

    result_alice = pipeline.answer(user="alice", message="anything")
    assert POISON_DOC in result_alice["sources"]
    assert CANARY_DOC in result_alice["sources"]

    # Bob sees the poison doc (it's public) but never the canary (it's Alice's private document).
    result_bob = pipeline.answer(user="bob", message="anything")
    assert POISON_DOC in result_bob["sources"]
    assert CANARY_DOC not in result_bob["sources"]

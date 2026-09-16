"""Guards the corpus invariants the LLM08 ground truth depends on.

Canary and poison must never share a document (a known llmsectest issue: poison output can mask
canary detection), and the secret must actually land in the system prompt. Nothing else in the
suite would catch a corpus edit that silently violated this.
"""

from __future__ import annotations

from pathlib import Path

from mloda_rag_testbed.corpus.loader import load_documents, load_system_prompt

_CANARY = "CANARY-TEST-VALUE"
_POISON = "POISON-TEST-VALUE"
_SECRET = "SECRET-TEST-VALUE"


def test_canary_appears_only_in_alice_payroll() -> None:
    docs = {doc["doc_id"]: doc["text"] for doc in load_documents(_CANARY, _POISON)}
    holders = [doc_id for doc_id, text in docs.items() if _CANARY in text]
    assert holders == ["alice_payroll"]


def test_poison_appears_only_in_pub_newsletter() -> None:
    docs = {doc["doc_id"]: doc["text"] for doc in load_documents(_CANARY, _POISON)}
    holders = [doc_id for doc_id, text in docs.items() if _POISON in text]
    assert holders == ["pub_newsletter"]


def test_canary_and_poison_documents_are_distinct() -> None:
    docs = {doc["doc_id"]: doc["text"] for doc in load_documents(_CANARY, _POISON)}
    canary_holders = {doc_id for doc_id, text in docs.items() if _CANARY in text}
    poison_holders = {doc_id for doc_id, text in docs.items() if _POISON in text}
    assert canary_holders.isdisjoint(poison_holders)


def test_secret_lands_in_system_prompt() -> None:
    assert _SECRET in load_system_prompt(_SECRET)


def test_system_prompt_override_with_stray_braces_does_not_raise(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("Note: use format {like this}. Secret: {secret}", encoding="utf-8")
    rendered = load_system_prompt(_SECRET, str(prompt_file))
    assert _SECRET in rendered
    assert "{like this}" in rendered

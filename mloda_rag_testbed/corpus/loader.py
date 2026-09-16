"""Loads the Example Bank corpus: documents, edges, authorization tuples, system prompt.

``{canary}``/``{poison}``/``{secret}`` placeholders in the packaged files are substituted here,
never hardcoded, so the planted values stay configurable via ``config.Settings``. Functions take
the specific strings they need rather than a ``Settings`` instance, so they are testable in
isolation with fixed values.
"""

from __future__ import annotations

import importlib.resources
import json
from typing import Any

_PACKAGE = "mloda_rag_testbed.corpus"


def _resource_text(name: str) -> str:
    return importlib.resources.files(_PACKAGE).joinpath(name).read_text(encoding="utf-8")


def load_documents(canary: str, poison: str) -> list[dict[str, Any]]:
    """Return the corpus documents with ``{canary}``/``{poison}`` substituted."""
    raw: list[dict[str, Any]] = json.loads(_resource_text("bank_documents.json"))
    return [{**doc, "text": doc["text"].format(canary=canary, poison=poison)} for doc in raw]


def load_edges() -> list[list[str]]:
    """Return the document adjacency list used by ``retrieval=graph``."""
    edges: list[list[str]] = json.loads(_resource_text("bank_edges.json"))
    return edges


def load_system_prompt(secret: str, override_path: str | None = None) -> str:
    """Return the system prompt with ``{secret}`` substituted.

    ``override_path`` reads an external file instead of the packaged one (``TESTBED_SYSTEM_PROMPT_FILE``).
    """
    if override_path:
        with open(override_path, encoding="utf-8") as fh:
            raw = fh.read()
    else:
        raw = _resource_text("system_prompt.txt")
    return raw.format(secret=secret)


def authz_tuples_path() -> str:
    """Return a real filesystem path to ``authz_tuples.json`` for open-kgo's ``locator`` credential.

    Assumes a non-zipped install (editable dev install or a normal wheel unpacked to site-packages),
    which is the only supported deployment for this repo; ``importlib.resources.files`` then returns
    a real ``Path`` directly.
    """
    return str(importlib.resources.files(_PACKAGE).joinpath("authz_tuples.json"))

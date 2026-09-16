"""Runtime configuration, read from environment variables.

``TESTBED_LLM`` (default ``codex``): ``codex``, ``mistral``, or ``fake``.
``TESTBED_RETRIEVAL`` (default ``bm25s``): ``bm25s``, ``graph``, or ``all`` (ground-truth, no ranking).
``TESTBED_AUTHZ`` (default ``on``): ``off`` skips the per-tenant authorization filter.
``TESTBED_SECRET`` / ``TESTBED_CANARY`` / ``TESTBED_POISON``: planted values; must match the
    scanner's ``--app-secret`` / ``--app-canary`` / ``--app-rag-poison``.
``TESTBED_DEFAULT_USER`` (default ``bob``): used when a request omits ``user``.
``TESTBED_TOP_K`` (default ``4``): passages per answer (bm25s/graph only; ``all`` ignores it).
``TESTBED_LLM_TIMEOUT`` (default ``75``): seconds, below the scanner's 90s default.
``TESTBED_LLM_MODEL`` (default unset): codex ``-m``; mistral via ``VIBE_ACTIVE_MODEL``.
``TESTBED_SYSTEM_PROMPT_FILE`` (default unset): overrides the packaged system prompt file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    llm: str = "codex"
    retrieval: str = "bm25s"
    authz: str = "on"
    secret: str = "SECRET-DEMO-7f2a"
    canary: str = "CANARY-EXAMPLEBANK-91ac"
    poison: str = "POISON-EXAMPLEBANK-3b9d"
    default_user: str = "bob"
    top_k: int = 4
    llm_timeout: float = 75.0
    llm_model: str | None = None
    system_prompt_file: str | None = None


def load_settings() -> Settings:
    """Read Settings from the environment. Call once per process (or per test)."""
    return Settings(
        llm=os.environ.get("TESTBED_LLM", "codex"),
        retrieval=os.environ.get("TESTBED_RETRIEVAL", "bm25s"),
        authz=os.environ.get("TESTBED_AUTHZ", "on"),
        secret=os.environ.get("TESTBED_SECRET", "SECRET-DEMO-7f2a"),
        canary=os.environ.get("TESTBED_CANARY", "CANARY-EXAMPLEBANK-91ac"),
        poison=os.environ.get("TESTBED_POISON", "POISON-EXAMPLEBANK-3b9d"),
        default_user=os.environ.get("TESTBED_DEFAULT_USER", "bob"),
        top_k=int(os.environ.get("TESTBED_TOP_K", "4")),
        llm_timeout=float(os.environ.get("TESTBED_LLM_TIMEOUT", "75")),
        llm_model=os.environ.get("TESTBED_LLM_MODEL") or None,
        system_prompt_file=os.environ.get("TESTBED_SYSTEM_PROMPT_FILE") or None,
    )

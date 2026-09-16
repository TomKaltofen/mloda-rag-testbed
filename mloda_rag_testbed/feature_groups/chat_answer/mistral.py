"""chat_answer backend "mistral": Mistral Vibe CLI, non-interactive one-shot, no tool execution.

``--disabled-tools '*'`` forces a pure LLM answer: Vibe is a coding agent by default, and without
this flag it could execute tools against the host in response to a successful prompt injection,
the same class of risk documented on the codex backend.
"""

from __future__ import annotations

import tempfile
from typing import ClassVar

from mloda_rag_testbed.config import load_settings
from mloda_rag_testbed.feature_groups.chat_answer.base import BaseChatAnswer
from mloda_rag_testbed.llm.cli import default_env, run_cli


class MistralChatAnswer(BaseChatAnswer):
    """Backend "mistral": ``vibe -p``. The answer is on stdout."""

    LLM_BACKENDS: ClassVar[dict[str, str]] = {"mistral": "Mistral Vibe CLI"}

    @classmethod
    def _complete(cls, prompt: str) -> str:
        settings = load_settings()
        with tempfile.TemporaryDirectory() as scratch_dir:
            argv = [
                "vibe",
                "-p",
                "--output",
                "text",
                "--max-turns",
                "1",
                "--trust",
                "--disabled-tools",
                "*",
                "--workdir",
                scratch_dir,
            ]
            env = default_env()
            if settings.llm_model:
                env["VIBE_ACTIVE_MODEL"] = settings.llm_model
            return run_cli(argv, prompt, timeout=settings.llm_timeout, cwd=scratch_dir, env=env)

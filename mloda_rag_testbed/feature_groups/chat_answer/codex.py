"""chat_answer backend "codex": OpenAI's codex CLI, non-interactive one-shot.

Security note: ``-s read-only`` still permits the agent to READ files reachable to this process
(only writes are blocked), so a successful prompt injection could exfiltrate readable host file
contents through the reply. ``--ignore-user-config``/``--ignore-rules`` skip ``config.toml`` and
execpolicy ``.rules`` specifically (not AGENTS.md discovery); ``CODEX_HOME`` is redirected into the
fresh, empty, per-call scratch directory so codex's own config/auth-cache discovery is scoped there
too, instead of the real ``~/.codex``. See the README's Security note before running this backend on
a host with anything sensitive reachable.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import ClassVar

from mloda_rag_testbed.config import load_settings
from mloda_rag_testbed.feature_groups.chat_answer.base import BaseChatAnswer
from mloda_rag_testbed.llm.cli import LlmUnavailableError, default_env, run_cli


class CodexChatAnswer(BaseChatAnswer):
    """Backend "codex": ``codex exec``. The answer is written to a file (``-o``), not stdout."""

    LLM_BACKENDS: ClassVar[dict[str, str]] = {"codex": "codex exec CLI"}

    @classmethod
    def _complete(cls, prompt: str) -> str:
        settings = load_settings()
        with tempfile.TemporaryDirectory() as scratch_dir:
            out_file = str(Path(scratch_dir) / "answer.txt")
            codex_home = Path(scratch_dir) / "codex_home"
            codex_home.mkdir()
            argv = [
                "codex",
                "exec",
                "-s",
                "read-only",
                "--skip-git-repo-check",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "-C",
                scratch_dir,
                "-o",
                out_file,
            ]
            if settings.llm_model:
                argv += ["-m", settings.llm_model]
            argv.append("-")

            env = default_env()
            env["CODEX_HOME"] = str(codex_home)
            run_cli(argv, prompt, timeout=settings.llm_timeout, cwd=scratch_dir, env=env)

            try:
                return Path(out_file).read_text(encoding="utf-8").strip()
            except FileNotFoundError as exc:
                raise LlmUnavailableError("codex exec exited 0 but wrote no output file.") from exc

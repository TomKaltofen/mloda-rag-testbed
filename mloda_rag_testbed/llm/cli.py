"""Run a coding-agent CLI as a one-shot subprocess.

Mirrors rag_integration's ``ClaudeCliResponse._call_claude_cli``: a fixed argv list (never
``shell=True``, never a user-controlled binary path), prompt on stdin, plain text out.
"""

from __future__ import annotations

import subprocess  # nosec B404
from collections.abc import Mapping


class LlmUnavailableError(RuntimeError):
    """The CLI binary is missing, exited non-zero, or timed out."""


def run_cli(
    argv: list[str],
    prompt: str,
    timeout: float,
    cwd: str | None = None,
    env: Mapping[str, str] | None = None,
) -> str:
    """Run ``argv`` with ``prompt`` on stdin; return stdout, stripped.

    Raises :class:`LlmUnavailableError` if the binary is not on PATH, exits non-zero, or times out.
    Callers whose CLI writes the answer elsewhere (a file, not stdout) read that file themselves;
    this function's return value is meaningful only for a stdout-based backend.
    """
    try:
        result = subprocess.run(  # nosec B603
            argv,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=dict(env) if env else None,
            check=False,
        )
    except FileNotFoundError as exc:
        raise LlmUnavailableError(f"CLI binary not found: {argv[0]!r} is not on PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        raise LlmUnavailableError(f"CLI call timed out after {timeout}s: {argv[0]!r}.") from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()[:2000]
        raise LlmUnavailableError(f"{argv[0]!r} exited {result.returncode}: {stderr}")

    return result.stdout.strip()

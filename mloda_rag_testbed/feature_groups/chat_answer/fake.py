"""Deterministic offline chat_answer backend, used by every offline test and by tox's default run."""

from __future__ import annotations

import re
from typing import ClassVar

from mloda_rag_testbed.feature_groups.chat_answer.base import BaseChatAnswer

_CONTEXT_LINE_RE = re.compile(r"^\[(?P<doc_id>[^\]]+)\] (?P<text>.*)$")


def _parse_context_passages(prompt: str) -> list[tuple[str, str]]:
    """Reconstruct (doc_id, text) pairs from build_prompt's Context block.

    A passage's own text may contain embedded newlines (build_prompt joins the whole prompt with
    "\\n"), so a non-matching, non-blank line continues the previous passage rather than being
    a new one; the block ends at the first blank line (build_prompt always appends one).
    """
    lines = prompt.splitlines()
    try:
        start = lines.index("Context:") + 1
    except ValueError:
        return []

    passages: list[tuple[str, list[str]]] = []
    for line in lines[start:]:
        if line == "":
            break
        match = _CONTEXT_LINE_RE.match(line)
        if match:
            passages.append((match.group("doc_id"), [match.group("text")]))
        elif passages:
            passages[-1][1].append(line)
    return [(doc_id, "\n".join(text_lines)) for doc_id, text_lines in passages]


class FakeChatAnswer(BaseChatAnswer):
    """Backend "fake": quotes back every passage's doc_id and a text snippet.

    No real model call. A passage whose text contains a line starting with ``SAY:`` makes the
    reply echo that line's remainder verbatim, so a test can force a deterministic reply without
    depending on real LLM compliance.
    """

    LLM_BACKENDS: ClassVar[dict[str, str]] = {"fake": "deterministic offline backend for tests"}

    @classmethod
    def _complete(cls, prompt: str) -> str:
        passages = _parse_context_passages(prompt)
        if not passages:
            return "No relevant documents found."

        reply = "Based on: " + ", ".join(f"{doc_id}: {text[:40]}" for doc_id, text in passages)
        for _, text in passages:
            for line in text.splitlines():
                if line.strip().startswith("SAY:"):
                    reply += " " + line.strip()[len("SAY:") :].strip()
        return reply

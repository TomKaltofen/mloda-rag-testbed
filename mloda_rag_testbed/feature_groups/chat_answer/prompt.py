"""Prompt assembly for chat_answer: system prompt + retrieved passages + the user's question.

Mirrors rag_integration's ``ClaudeCliResponse._build_prompt`` (system / Context / Question
sections joined by newlines), the established convention in this ecosystem.
"""

from __future__ import annotations

from typing import Any


def build_prompt(system_prompt: str, passages: list[dict[str, Any]], query_text: str) -> str:
    parts: list[str] = [system_prompt, ""]
    if passages:
        parts.append("Context:")
        for passage in passages:
            parts.append(f"[{passage.get('doc_id')}] {passage.get('text')}")
        parts.append("")
    parts.append("Question:")
    parts.append(query_text)
    return "\n".join(parts)

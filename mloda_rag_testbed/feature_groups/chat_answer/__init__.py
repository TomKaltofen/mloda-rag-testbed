"""The ``chat_answer`` family: retrieval + prompt assembly + an LLM CLI backend -> an answer."""

from __future__ import annotations

from mloda_rag_testbed.feature_groups.chat_answer.base import BaseChatAnswer, ChatAnswerError
from mloda_rag_testbed.feature_groups.chat_answer.codex import CodexChatAnswer
from mloda_rag_testbed.feature_groups.chat_answer.fake import FakeChatAnswer
from mloda_rag_testbed.feature_groups.chat_answer.mistral import MistralChatAnswer

__all__ = ["BaseChatAnswer", "ChatAnswerError", "CodexChatAnswer", "FakeChatAnswer", "MistralChatAnswer"]

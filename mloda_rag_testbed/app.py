"""FastAPI app: POST /chat, GET /health.

The llmsectest target contract: POST a JSON body, top-level "reply" in the response, no auth, no
rate limiting, and the app must never accept a "system" field from the request (it supplies its
own system prompt). Model failure returns HTTP 500, the code the contract documents as making a
probe "inconclusive" rather than a false "withstood".
"""

from __future__ import annotations

import shutil
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, model_validator

from mloda_rag_testbed import pipeline
from mloda_rag_testbed.config import load_settings
from mloda_rag_testbed.feature_groups.chat_answer.base import ChatAnswerError
from mloda_rag_testbed.llm.cli import LlmUnavailableError

app = FastAPI(title="mloda-rag-testbed")

_HEALTH_BINARY = {"codex": "codex", "mistral": "vibe", "fake": None}


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    message: str
    user: str | None = None
    conversation_id: str | None = None

    @model_validator(mode="after")
    def _reject_system_field(self) -> ChatRequest:
        if self.model_extra and "system" in self.model_extra:
            raise ValueError("the 'system' field is not accepted; this app supplies its own system prompt")
        return self


@app.post("/chat")
def chat(payload: ChatRequest) -> dict[str, Any]:
    settings = load_settings()
    user = payload.user or settings.default_user
    try:
        result = pipeline.answer(user=user, message=payload.message)
    except (LlmUnavailableError, ChatAnswerError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if payload.conversation_id:
        result["conversation_id"] = payload.conversation_id
    return result


@app.get("/health")
def health() -> dict[str, Any]:
    settings = load_settings()
    binary = _HEALTH_BINARY[settings.llm]
    llm_binary_found = binary is None or shutil.which(binary) is not None
    return {
        "llm_backend": settings.llm,
        "retrieval": settings.retrieval,
        "authz": settings.authz,
        "llm_binary_found": llm_binary_found,
    }

# DEPRECATED: No longer the primary interface.
# Use Claude Code with the legal-rag MCP server (mcp_server.py + .mcp.json) instead.
# Kept for potential future web UI / Open WebUI integration.
"""
Agent One API — OpenAI-compatible REST API server.
Exposes /v1/models and /v1/chat/completions so Open WebUI can connect.
RAG (Supabase search) always runs regardless of which LLM is selected.
"""

import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(".env")

from agent import OLLAMA_MODELS, close_db, get_agent, initialize_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_db()
    yield
    await close_db()


app = FastAPI(title="Agent One API", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Models endpoint
# ---------------------------------------------------------------------------

@app.get("/v1/models")
async def list_models():
    default_model = os.getenv("LLM_CHOICE", "gpt-4o-mini")
    agent_name = os.getenv("AGENT_NAME", "Knowledge Assistant")
    models = [
        {
            "id": default_model,
            "object": "model",
            "created": 1700000000,
            "owned_by": "agent-one",
            "name": agent_name,
        }
    ]
    for m in OLLAMA_MODELS:
        models.append(
            {"id": m, "object": "model", "created": 1700000000, "owned_by": "ollama", "name": m}
        )
    return {"object": "list", "data": models}


# ---------------------------------------------------------------------------
# Chat completions endpoint
# ---------------------------------------------------------------------------

class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[Message]
    stream: bool = True


async def _stream_openai(messages: list[Message], model_id: str) -> AsyncIterator[str]:
    rag_agent = get_agent(model_id)

    user_message = next(
        (m.content for m in reversed(messages) if m.role == "user"), ""
    )
    logger.info(f"Chat request | model={model_id} | query={user_message[:80]!r}")

    completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    created = int(time.time())

    try:
        async with rag_agent.run_stream(user_message) as result:
            async for text in result.stream_text(delta=True):
                chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model_id,
                    "choices": [{"index": 0, "delta": {"content": text}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(chunk)}\n\n"
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        error_chunk = {
            "id": completion_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model_id,
            "choices": [{"index": 0, "delta": {"content": f"[Error: {e}]"}, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"

    final_chunk = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model_id,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(final_chunk)}\n\n"
    yield "data: [DONE]\n\n"


@app.post("/v1/chat/completions")
async def openai_chat(request: ChatRequest):
    logger.info(f"POST /v1/chat/completions model={request.model} msgs={len(request.messages)}")
    return StreamingResponse(
        _stream_openai(request.messages, request.model),
        media_type="text/event-stream",
    )

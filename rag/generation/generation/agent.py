"""
Generation layer — PydanticAI RAG agent with OpenAI and Ollama support.
Embeddings always use OpenAI; the LLM backend is switchable via model_id.
"""

import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent

from generation.prompts import SYSTEM_PROMPT
from retrieval.search import search_knowledge_base
from storage.db_utils import initialize_database, close_database

load_dotenv(".env")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://172.17.0.1:11435")
OLLAMA_MODELS = [m.strip() for m in os.getenv("OLLAMA_MODELS", "").split(",") if m.strip()]


async def initialize_db():
    """Initialise the shared database connection pool."""
    await initialize_database()


async def close_db():
    """Close the shared database connection pool."""
    await close_database()


def build_agent(model_id: str | None = None) -> Agent:
    if model_id is None:
        model_id = os.getenv("LLM_CHOICE", "gpt-4o-mini")

    if model_id in OLLAMA_MODELS:
        from pydantic_ai.models.openai import OpenAIModel
        ollama_client = AsyncOpenAI(base_url=f"{OLLAMA_BASE_URL}/v1", api_key="ollama")
        model = OpenAIModel(model_id, openai_client=ollama_client)
    else:
        model = f"openai:{model_id}"

    return Agent(model, system_prompt=SYSTEM_PROMPT, tools=[search_knowledge_base])


def get_agent(model_id: str) -> Agent:
    return build_agent(model_id)


# Default agent instance (used by CLI and the default /chat endpoint)
agent = build_agent()

"""
Root shim — re-exports from generation.agent so main.py imports remain stable.
All implementation lives in generation/agent.py.
"""
from generation.agent import OLLAMA_MODELS, agent, build_agent, close_db, get_agent, initialize_db

__all__ = ["OLLAMA_MODELS", "agent", "build_agent", "close_db", "get_agent", "initialize_db"]

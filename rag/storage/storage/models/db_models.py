"""Database ORM models."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum


class MessageRole(str, Enum):
    """Message role enum."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Document(BaseModel):
    """Document model."""
    id: Optional[str] = None
    title: str
    source: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Chunk(BaseModel):
    """Document chunk model."""
    id: Optional[str] = None
    document_id: str
    content: str
    embedding: Optional[List[float]] = None
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    token_count: Optional[int] = None
    created_at: Optional[datetime] = None

    @field_validator('embedding')
    @classmethod
    def validate_embedding(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        """Validate embedding dimensions."""
        if v is not None and len(v) != 1536:  # OpenAI text-embedding-3-small
            raise ValueError(f"Embedding must have 1536 dimensions, got {len(v)}")
        return v


class Session(BaseModel):
    """Session model."""
    id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class Message(BaseModel):
    """Message model."""
    id: Optional[str] = None
    session_id: str
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)

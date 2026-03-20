"""API request/response and agent models."""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum

from storage.models.db_models import Message


class SearchType(str, Enum):
    """Search type enum."""
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., description="Search query")
    search_type: SearchType = Field(default=SearchType.SEMANTIC, description="Type of search")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")

    model_config = ConfigDict(use_enum_values=True)


class DocumentMetadata(BaseModel):
    """Document metadata model."""
    id: str
    title: str
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    chunk_count: Optional[int] = None


class ChunkResult(BaseModel):
    """Chunk search result model."""
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document_title: str
    document_source: str

    @field_validator('score')
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Ensure score is between 0 and 1."""
        return max(0.0, min(1.0, v))


class SearchResponse(BaseModel):
    """Search response model."""
    results: List[ChunkResult] = Field(default_factory=list)
    total_results: int = 0
    search_type: SearchType
    query_time_ms: float


class ToolCall(BaseModel):
    """Tool call information model."""
    tool_name: str
    args: Dict[str, Any] = Field(default_factory=dict)
    tool_call_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    message: str
    session_id: str
    sources: List[DocumentMetadata] = Field(default_factory=list)
    tools_used: List[ToolCall] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamDelta(BaseModel):
    """Streaming response delta."""
    content: str
    delta_type: Literal["text", "tool_call", "end"] = "text"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentDependencies(BaseModel):
    """Dependencies for the agent."""
    session_id: str
    database_url: Optional[str] = None
    openai_api_key: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentContext(BaseModel):
    """Agent execution context."""
    session_id: str
    messages: List[Message] = Field(default_factory=list)
    tool_calls: List[ToolCall] = Field(default_factory=list)
    search_results: List[ChunkResult] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

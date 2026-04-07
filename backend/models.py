from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid


class ReasoningStep(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_type: str  # decomposition, reflection, verification, synthesis
    content: str
    tokens_used: int = 0
    latency_ms: int = 0
    confidence: float = 0.0
    parent_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReasoningSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    max_depth: int = 3
    model: str = "gpt-4o-mini"
    status: str = "pending"  # pending, processing, completed, error
    final_answer: Optional[str] = None
    steps: List[ReasoningStep] = []
    total_tokens: int = 0
    total_latency_ms: int = 0
    recursion_depth: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class SessionCreate(BaseModel):
    query: str
    max_depth: int = 3
    model: str = "gpt-4o-mini"


class WebSocketMessage(BaseModel):
    type: str  # step_update, status_change, completion, error
    session_id: str
    data: Dict[str, Any]

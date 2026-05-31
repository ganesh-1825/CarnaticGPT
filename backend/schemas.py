from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    user_id: int

class ChatQueryRequest(BaseModel):
    conversation_id: str
    message: str

class CitationItem(BaseModel):
    chunk_id: str
    text: str
    source: str
    book_name: str
    page: int
    score: float
    confidence: Optional[Union[str, float]] = None

class ChatQueryResponse(BaseModel):
    response: str
    citations: List[CitationItem]
    confidence: Optional[Union[str, float]] = None
    detected_raga: Optional[str] = None


class FeedbackRequest(BaseModel):
    message_id: int
    rating: int = Field(..., description="1 for Upvote, -1 for Downvote")
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    status: str
    message: str

class MessageItem(BaseModel):
    id: int
    sender: str
    content: str
    citations: Optional[Any] = None
    confidence: Optional[Union[str, float]] = None
    created_at: str

class ConversationItem(BaseModel):
    id: str
    title: str
    created_at: str

class DashboardStats(BaseModel):
    total_queries: int
    avg_latency_ms: int
    total_chunks: int
    upvotes: int
    downvotes: int
    raga_distribution: Dict[str, int]
    usage_trend: List[Dict[str, Any]]

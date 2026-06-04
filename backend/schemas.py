from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(None, description="Optional email address")
    full_name: str = Field(None, description="User's full name")
    password: str = Field(..., min_length=4)

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    user_id: int
    full_name: Optional[str] = None
    email: Optional[str] = None

class UserProfile(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    preferences: Optional[Any] = None
    theme: Optional[str] = None
    created_at: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=4)

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
    is_pinned: bool = False
    created_at: str
    updated_at: Optional[str] = None

class RenameConversationRequest(BaseModel):
    title: str

class DashboardStats(BaseModel):
    total_queries: int
    avg_latency_ms: int
    total_chunks: int
    upvotes: int
    downvotes: int
    raga_distribution: Dict[str, int]
    usage_trend: List[Dict[str, Any]]

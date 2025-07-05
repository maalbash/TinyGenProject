"""
Database models for Supabase integration.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum

class RequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class DiffRequestRecord(BaseModel):
    """Model for storing diff requests in the database."""
    id: Optional[str] = None
    repo_url: str
    prompt: str
    enable_reflection: bool
    status: RequestStatus
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Request metadata
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    user_id: Optional[str] = None  # For future user tracking
    
    # Processing results
    initial_diff: Optional[str] = None
    final_diff: Optional[str] = None
    reflection_applied: bool = False
    original_diff: Optional[str] = None
    
    # GitHub integration results
    branch_name: Optional[str] = None
    pull_request_url: Optional[str] = None
    
    # Error handling
    error_message: Optional[str] = None
    error_details: Optional[str] = None
    
    # Performance metrics
    processing_time_seconds: Optional[float] = None
    openai_tokens_used: Optional[int] = None
    
    class Config:
        use_enum_values = True

class DiffRequestCreate(BaseModel):
    """Model for creating new diff requests."""
    repo_url: str
    prompt: str
    enable_reflection: bool = False
    user_id: Optional[str] = None

class DiffRequestUpdate(BaseModel):
    """Model for updating existing diff requests."""
    status: Optional[RequestStatus] = None
    initial_diff: Optional[str] = None
    final_diff: Optional[str] = None
    reflection_applied: Optional[bool] = None
    original_diff: Optional[str] = None
    branch_name: Optional[str] = None
    pull_request_url: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    openai_tokens_used: Optional[int] = None
    
    class Config:
        use_enum_values = True
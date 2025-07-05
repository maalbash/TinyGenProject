"""
Pydantic models for the Repo Diff Generator API.
"""

from typing import Optional
from pydantic import BaseModel, Field

class DiffRequest(BaseModel):
    repoUrl: str = Field(..., description="GitHub repository URL")
    prompt: str = Field(..., description="Textual command for changes")
    enableReflection: bool = Field(False, description="Enable AI reflection to improve generated diff (default: false)")

class DiffResponse(BaseModel):
    diff: str = Field(..., description="Unified diff string")
    reflection_applied: bool = Field(..., description="Whether reflection resulted in changes")
    original_diff: Optional[str] = Field(None, description="Original diff before reflection")
    pull_request_url: Optional[str] = Field(None, description="URL of the created pull request")
    branch_name: str = Field(..., description="Name of the branch created for changes")
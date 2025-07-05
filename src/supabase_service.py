"""
Supabase service for database operations.
"""

import os
import logging
import uuid
from typing import Optional, List
from datetime import datetime
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from fastapi import HTTPException
from database_models import DiffRequestRecord, DiffRequestCreate, DiffRequestUpdate, RequestStatus

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables are required")

        options = ClientOptions(
            schema='public',
            headers={},
            auto_refresh_token=True,
            persist_session=True,
        )
        self.client: Client = create_client(self.supabase_url, self.supabase_key, options=options)
        self.table_name = "diff_requests"
    
    async def create_request(self, request_data: DiffRequestCreate, repo_owner: str, repo_name: str) -> str:
        """Create a new diff request record."""
        try:
            record_id = str(uuid.uuid4())
            
            data = {
                "id": record_id,
                "repo_url": request_data.repo_url,
                "prompt": request_data.prompt,
                "enable_reflection": request_data.enable_reflection,
                "status": RequestStatus.PENDING.value,
                "repo_owner": repo_owner,
                "repo_name": repo_name,
                "user_id": request_data.user_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
            
            result = self.client.table(self.table_name).insert(data).execute()
            
            if result.data:
                logger.info(f"Created diff request record: {record_id}")
                return record_id
            else:
                raise Exception("Failed to create record")
                
        except Exception as e:
            logger.error(f"Error creating diff request record: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create database record: {str(e)}")
    
    async def update_request(self, request_id: str, updates: DiffRequestUpdate) -> bool:
        """Update an existing diff request record."""
        try:
            # Prepare update data, excluding None values
            update_data = {k: v for k, v in updates.dict().items() if v is not None}
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table(self.table_name).update(update_data).eq("id", request_id).execute()
            
            if result.data:
                logger.info(f"Updated diff request record: {request_id}")
                return True
            else:
                logger.warning(f"No record found to update: {request_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating diff request record {request_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update database record: {str(e)}")
    
    async def get_request(self, request_id: str) -> Optional[DiffRequestRecord]:
        """Get a diff request record by ID."""
        try:
            result = self.client.table(self.table_name).select("*").eq("id", request_id).execute()
            
            if result.data:
                return DiffRequestRecord(**result.data[0])
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting diff request record {request_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get database record: {str(e)}")
    
    async def get_requests_by_repo(self, repo_owner: str, repo_name: str, limit: int = 50) -> List[DiffRequestRecord]:
        """Get diff requests for a specific repository."""
        try:
            result = (self.client.table(self.table_name)
                     .select("*")
                     .eq("repo_owner", repo_owner)
                     .eq("repo_name", repo_name)
                     .order("created_at", desc=True)
                     .limit(limit)
                     .execute())
            
            return [DiffRequestRecord(**record) for record in result.data]
            
        except Exception as e:
            logger.error(f"Error getting requests for repo {repo_owner}/{repo_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get repository records: {str(e)}")
    
    async def get_recent_requests(self, limit: int = 100) -> List[DiffRequestRecord]:
        """Get recent diff requests."""
        try:
            result = (self.client.table(self.table_name)
                     .select("*")
                     .order("created_at", desc=True)
                     .limit(limit)
                     .execute())
            
            return [DiffRequestRecord(**record) for record in result.data]
            
        except Exception as e:
            logger.error(f"Error getting recent requests: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get recent records: {str(e)}")
    
    async def mark_as_processing(self, request_id: str) -> bool:
        """Mark a request as processing."""
        updates = DiffRequestUpdate(status=RequestStatus.PROCESSING)
        return await self.update_request(request_id, updates)
    
    async def mark_as_completed(self, request_id: str, final_diff: str, reflection_applied: bool = False, 
                               original_diff: Optional[str] = None, branch_name: Optional[str] = None,
                               pull_request_url: Optional[str] = None, processing_time: Optional[float] = None,
                               tokens_used: Optional[int] = None) -> bool:
        """Mark a request as completed with results."""
        updates = DiffRequestUpdate(
            status=RequestStatus.COMPLETED,
            final_diff=final_diff,
            reflection_applied=reflection_applied,
            original_diff=original_diff,
            branch_name=branch_name,
            pull_request_url=pull_request_url,
            processing_time_seconds=processing_time,
            openai_tokens_used=tokens_used
        )
        return await self.update_request(request_id, updates)
    
    async def mark_as_failed(self, request_id: str, error_message: str, error_details: Optional[str] = None) -> bool:
        """Mark a request as failed with error details."""
        updates = DiffRequestUpdate(
            status=RequestStatus.FAILED,
            error_message=error_message,
            error_details=error_details
        )
        return await self.update_request(request_id, updates)
    
    async def get_usage_stats(self) -> dict:
        """Get usage statistics."""
        try:
            # Get total requests
            total_result = self.client.table(self.table_name).select("id", count="exact").execute()
            total_requests = total_result.count
            
            # Get completed requests
            completed_result = (self.client.table(self.table_name)
                              .select("id", count="exact")
                              .eq("status", RequestStatus.COMPLETED.value)
                              .execute())
            completed_requests = completed_result.count
            
            # Get failed requests
            failed_result = (self.client.table(self.table_name)
                           .select("id", count="exact")
                           .eq("status", RequestStatus.FAILED.value)
                           .execute())
            failed_requests = failed_result.count
            
            # Get requests with reflection
            reflection_result = (self.client.table(self.table_name)
                               .select("id", count="exact")
                               .eq("reflection_applied", True)
                               .execute())
            reflection_requests = reflection_result.count
            
            return {
                "total_requests": total_requests,
                "completed_requests": completed_requests,
                "failed_requests": failed_requests,
                "pending_requests": total_requests - completed_requests - failed_requests,
                "reflection_requests": reflection_requests,
                "success_rate": (completed_requests / total_requests * 100) if total_requests > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get usage statistics: {str(e)}")
"""
GitHub API integration for creating branches and pull requests.
"""

import os
import re
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class GitHubService:
    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
    
    def _get_headers(self) -> dict:
        """Get headers for GitHub API requests."""
        return {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "repo-diff-api"
        }
    
    def parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """Parse GitHub repository URL to extract owner and repo name."""
        # Handle various GitHub URL formats
        patterns = [
            r"https://github\.com/([^/]+)/([^/]+)(?:\.git)?/?$",
            r"git@github\.com:([^/]+)/([^/]+)(?:\.git)?$"
        ]
        
        for pattern in patterns:
            match = re.match(pattern, repo_url.strip())
            if match:
                owner, repo = match.groups()
                # Remove .git suffix if present
                repo = repo.replace('.git', '')
                return owner, repo
        
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
    
    async def get_default_branch(self, owner: str, repo: str) -> str:
        """Get the default branch of the repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get repository info: {response.text}"
                )
            
            repo_data = response.json()
            return repo_data["default_branch"]
    
    async def get_branch_sha(self, owner: str, repo: str, branch: str) -> str:
        """Get the SHA of the latest commit on a branch."""
        url = f"{self.base_url}/repos/{owner}/{repo}/git/refs/heads/{branch}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get branch SHA: {response.text}"
                )
            
            ref_data = response.json()
            return ref_data["object"]["sha"]
    
    async def create_branch(self, owner: str, repo: str, branch_name: str, base_sha: str) -> bool:
        """Create a new branch from the given SHA."""
        url = f"{self.base_url}/repos/{owner}/{repo}/git/refs"
        
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=self._get_headers())
            
            if response.status_code == 201:
                logger.info(f"Created branch: {branch_name}")
                return True
            elif response.status_code == 422:
                # Branch already exists
                logger.info(f"Branch {branch_name} already exists")
                return True
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create branch: {response.text}"
                )
    
    async def get_file_content(self, owner: str, repo: str, file_path: str, branch: str) -> Tuple[str, str]:
        """Get file content and SHA for a specific file."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
        params = {"ref": branch}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=self._get_headers())
            
            if response.status_code == 200:
                file_data = response.json()
                import base64
                content = base64.b64decode(file_data["content"]).decode("utf-8")
                return content, file_data["sha"]
            elif response.status_code == 404:
                # File doesn't exist
                return "", ""
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to get file content: {response.text}"
                )
    
    async def update_file(self, owner: str, repo: str, file_path: str, content: str, 
                         branch: str, commit_message: str, file_sha: Optional[str] = None) -> bool:
        """Update or create a file in the repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
        
        import base64
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        data = {
            "message": commit_message,
            "content": encoded_content,
            "branch": branch
        }
        
        if file_sha:
            data["sha"] = file_sha
        
        async with httpx.AsyncClient() as client:
            response = await client.put(url, json=data, headers=self._get_headers())
            
            if response.status_code in [200, 201]:
                logger.info(f"Updated file: {file_path}")
                return True
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to update file {file_path}: {response.text}"
                )
    
    async def create_pull_request(self, owner: str, repo: str, branch_name: str, 
                                 base_branch: str, title: str, body: str) -> str:
        """Create a pull request."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        
        data = {
            "title": title,
            "body": body,
            "head": branch_name,
            "base": base_branch
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=self._get_headers())
            
            if response.status_code == 201:
                pr_data = response.json()
                logger.info(f"Created pull request: {pr_data['html_url']}")
                return pr_data["html_url"]
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create pull request: {response.text}"
                )
    
    async def check_repository_access(self, owner: str, repo: str) -> bool:
        """Check if we have write access to the repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                repo_data = response.json()
                # Check if we have push access
                permissions = repo_data.get("permissions", {})
                return permissions.get("push", False)
            else:
                return False
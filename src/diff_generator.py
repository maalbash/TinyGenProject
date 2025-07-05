"""
Core diff generation service that orchestrates the entire workflow.
"""

import os
import tempfile
import shutil
import logging
import time
import uuid
from datetime import datetime
from models import DiffRequest, DiffResponse
from repo_service import clone_repository, get_repo_structure, read_file_contents
from llm_service import generate_initial_diff, reflect_on_diff
from github_service import GitHubService
from diff_applier import DiffApplier
from supabase_service import SupabaseService
from database_models import DiffRequestCreate, DiffRequestUpdate, RequestStatus

logger = logging.getLogger(__name__)

async def generate_diff(request: DiffRequest) -> DiffResponse:
    """Generate a unified diff for the given repository and prompt."""
    temp_dir = None
    github_service = GitHubService()
    diff_applier = DiffApplier()
    supabase_service = SupabaseService()
    
    # Track processing time
    start_time = time.time()
    request_id = None
    
    try:
        # Parse repository info
        owner, repo = github_service.parse_repo_url(request.repoUrl)
        
        # Create database record
        db_request = DiffRequestCreate(
            repo_url=request.repoUrl,
            prompt=request.prompt,
            enable_reflection=request.enableReflection
        )
        request_id = await supabase_service.create_request(db_request, owner, repo)
        
        # Mark as processing
        await supabase_service.mark_as_processing(request_id)
        
        # Create temporary directory for cloning
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temp directory: {temp_dir}")
        
        # Check repository access
        has_access = await github_service.check_repository_access(owner, repo)
        if not has_access:
            error_msg = f"No write access to repository {owner}/{repo}. Make sure the GitHub token has appropriate permissions."
            await supabase_service.mark_as_failed(request_id, error_msg)
            raise Exception(error_msg)
        
        # Clone repository
        await clone_repository(request.repoUrl, temp_dir)
        
        # Get repository structure
        repo_structure = get_repo_structure(temp_dir)
        
        # Read key file contents
        key_files = repo_structure.split('\n')[:20]  # Limit to first 20 files
        file_contents = read_file_contents(temp_dir, key_files)
        
        # Generate initial diff
        logger.info("Generating initial diff...")
        initial_diff = await generate_initial_diff(repo_structure, file_contents, request.prompt)
        
        # Store initial diff in database
        await supabase_service.update_request(request_id, DiffRequestUpdate(initial_diff=initial_diff))
        
        # Initialize response values
        final_diff = initial_diff
        reflection_applied = False
        original_diff = None
        
        # Run reflection only if enabled
        if request.enableReflection:
            logger.info("Reflection enabled - running reflection...")
            reflection = await reflect_on_diff(initial_diff, repo_structure, request.prompt)
            
            # Determine final diff
            if reflection.get("needs_changes", False):
                final_diff = reflection.get("improved_diff", initial_diff)
                reflection_applied = True
                original_diff = initial_diff
                logger.info("Reflection suggested improvements, using improved diff")
            else:
                logger.info("Reflection approved original diff")
        else:
            logger.info("Reflection disabled - using initial diff")
        
        # Create branch and apply changes
        branch_name = f"ai-changes-{uuid.uuid4().hex[:8]}"
        pull_request_url = await apply_diff_and_create_pr(
            github_service, diff_applier, owner, repo, branch_name, final_diff, request.prompt
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Mark as completed in database
        await supabase_service.mark_as_completed(
            request_id=request_id,
            final_diff=final_diff,
            reflection_applied=reflection_applied,
            original_diff=original_diff,
            branch_name=branch_name,
            pull_request_url=pull_request_url,
            processing_time=processing_time
        )
        
        logger.info(f"Successfully processed request {request_id} in {processing_time:.2f}s")
        
        return DiffResponse(
            diff=final_diff,
            reflection_applied=reflection_applied,
            original_diff=original_diff,
            pull_request_url=pull_request_url,
            branch_name=branch_name
        )
        
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        
        # Mark as failed in database if we have a request_id
        if request_id:
            await supabase_service.mark_as_failed(
                request_id=request_id,
                error_message=str(e),
                error_details=f"Error occurred after {time.time() - start_time:.2f}s"
            )
        
        raise e
        
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp directory: {temp_dir}")

async def apply_diff_and_create_pr(github_service: GitHubService, diff_applier: DiffApplier, 
                                  owner: str, repo: str, branch_name: str, 
                                  diff_content: str, prompt: str) -> str:
    """Apply the diff to a new branch and create a pull request."""
    
    # Get default branch
    default_branch = await github_service.get_default_branch(owner, repo)
    
    # Get latest commit SHA
    base_sha = await github_service.get_branch_sha(owner, repo, default_branch)
    
    # Create new branch
    await github_service.create_branch(owner, repo, branch_name, base_sha)
    
    # Parse diff to get file changes
    file_changes = diff_applier.extract_file_changes_from_diff(diff_content)
    
    if not file_changes:
        logger.warning("No file changes found in diff")
        # Still create PR with just the diff as description
        pr_title = f"AI-generated changes: {prompt[:50]}..."
        pr_body = f"""This pull request was automatically generated based on the prompt:

**Prompt:** {prompt}

**Generated Diff:**
```diff
{diff_content}
```

Note: The diff could not be automatically applied. Please review and apply changes manually.
"""
        
        return await github_service.create_pull_request(
            owner, repo, branch_name, default_branch, pr_title, pr_body
        )
    
    # Apply changes to each file
    commit_message = f"AI-generated changes: {prompt[:50]}..."
    
    for file_path, new_content in file_changes.items():
        try:
            # Get existing file content and SHA
            existing_content, file_sha = await github_service.get_file_content(
                owner, repo, file_path, default_branch
            )
            
            # If it's a new file, file_sha will be empty
            if not file_sha and not existing_content:
                logger.info(f"Creating new file: {file_path}")
                await github_service.update_file(
                    owner, repo, file_path, new_content, branch_name, commit_message
                )
            else:
                # Update existing file
                logger.info(f"Updating existing file: {file_path}")
                # For existing files, we might need to apply the diff more carefully
                # For now, we'll use the new content directly
                await github_service.update_file(
                    owner, repo, file_path, new_content, branch_name, commit_message, file_sha
                )
                
        except Exception as e:
            logger.error(f"Failed to update file {file_path}: {e}")
            continue
    
    # Create pull request
    pr_title = f"AI-generated changes: {prompt[:50]}..."
    pr_body = f"""This pull request was automatically generated based on the prompt:

**Prompt:** {prompt}

**Changes made:**
{chr(10).join(f"- {file_path}" for file_path in file_changes.keys())}

**Generated Diff:**
```diff
{diff_content}
```

Please review the changes carefully before merging.
"""
    
    return await github_service.create_pull_request(
        owner, repo, branch_name, default_branch, pr_title, pr_body
    )
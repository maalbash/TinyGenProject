"""
Repository handling utilities for cloning and analyzing GitHub repositories.
"""

import os
import logging
from pathlib import Path
from typing import List
from fastapi import HTTPException
import git

logger = logging.getLogger(__name__)

async def clone_repository(repo_url: str, target_dir: str) -> None:
    """Clone a GitHub repository to the target directory."""
    try:
        # Use git.Repo.clone_from for better error handling
        git.Repo.clone_from(repo_url, target_dir, depth=1)
        logger.info(f"Successfully cloned {repo_url} to {target_dir}")
    except Exception as e:
        logger.error(f"Failed to clone repository: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to clone repository: {str(e)}")

def get_repo_structure(repo_path: str, max_files: int = 50) -> str:
    """Get a string representation of the repository structure."""
    structure = []
    repo_path_obj = Path(repo_path)
    
    # Common files to prioritize
    priority_files = [
        'README.md', 'README.txt', 'README.rst',
        'requirements.txt', 'setup.py', 'package.json',
        'Dockerfile', 'docker-compose.yml',
        'main.py', 'app.py', 'index.js', 'index.html'
    ]
    
    # Get priority files first
    found_files = []
    for priority_file in priority_files:
        file_path = repo_path_obj / priority_file
        if file_path.exists() and file_path.is_file():
            found_files.append(str(file_path.relative_to(repo_path_obj)))
    
    # Get other files
    for root, dirs, files in os.walk(repo_path):
        # Skip common unimportant directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in [
            'node_modules', '__pycache__', '.venv', 'venv', 'env',
            '.git', 'dist', 'build', 'target'
        ]]
        
        root_path = Path(root)
        for file in files:
            if len(found_files) >= max_files:
                break
                
            file_path = root_path / file
            rel_path = str(file_path.relative_to(repo_path))
            
            # Skip binary files and common unimportant files
            if (not file.startswith('.') and 
                not file.endswith(('.pyc', '.pyo', '.so', '.dylib', '.dll', '.exe', 
                                 '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.tar.gz')) and
                rel_path not in found_files):
                found_files.append(rel_path)
    
    return '\n'.join(sorted(found_files))

def read_file_contents(repo_path: str, file_paths: List[str], max_chars: int = 50000) -> str:
    """Read contents of specified files up to max_chars."""
    contents = []
    total_chars = 0
    
    for file_path in file_paths:
        full_path = Path(repo_path) / file_path
        if full_path.exists() and full_path.is_file():
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if total_chars + len(content) > max_chars:
                        remaining = max_chars - total_chars
                        content = content[:remaining] + "\n... (truncated)"
                    
                    contents.append(f"=== {file_path} ===\n{content}\n")
                    total_chars += len(content)
                    
                    if total_chars >= max_chars:
                        break
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")
    
    return '\n'.join(contents)
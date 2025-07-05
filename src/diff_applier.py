"""
Utility to parse and apply unified diffs to files.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

class DiffApplier:
    def __init__(self):
        pass
    
    def parse_unified_diff(self, diff_content: str) -> Dict[str, str]:
        """Parse unified diff and return a dictionary of file changes."""
        changes = {}
        
        # Split diff into individual file changes
        file_sections = re.split(r'^--- ', diff_content, flags=re.MULTILINE)
        
        for section in file_sections:
            if not section.strip():
                continue
                
            # Add back the --- that was removed by split
            if not section.startswith('---'):
                section = '--- ' + section
            
            file_change = self._parse_file_diff(section)
            if file_change:
                file_path, new_content = file_change
                changes[file_path] = new_content
        
        return changes
    
    def _parse_file_diff(self, diff_section: str) -> Optional[Tuple[str, str]]:
        """Parse a single file's diff section."""
        lines = diff_section.split('\n')
        
        # Find file path from headers
        file_path = None
        for line in lines:
            if line.startswith('--- a/'):
                file_path = line[6:]  # Remove '--- a/'
                break
            elif line.startswith('--- '):
                # Handle cases without a/ prefix
                path = line[4:]
                if path != '/dev/null':
                    file_path = path
                    break
        
        if not file_path:
            logger.warning("Could not extract file path from diff section")
            return None
        
        # Apply the diff changes
        try:
            new_content = self._apply_hunks(lines)
            return file_path, new_content
        except Exception as e:
            logger.error(f"Failed to apply diff for {file_path}: {e}")
            return None
    
    def _apply_hunks(self, diff_lines: List[str]) -> str:
        """Apply diff hunks to reconstruct the file content."""
        result_lines = []
        
        # Find the start of hunks (after the +++ line)
        hunk_start = 0
        for i, line in enumerate(diff_lines):
            if line.startswith('+++'):
                hunk_start = i + 1
                break
        
        # Process each hunk
        i = hunk_start
        while i < len(diff_lines):
            line = diff_lines[i]
            
            if line.startswith('@@'):
                # This is a hunk header, skip it
                i += 1
                continue
            elif line.startswith('-'):
                # Skip removed lines
                i += 1
                continue
            elif line.startswith('+'):
                # Add new lines
                result_lines.append(line[1:])  # Remove the '+' prefix
                i += 1
            elif line.startswith(' '):
                # Context line (unchanged)
                result_lines.append(line[1:])  # Remove the ' ' prefix
                i += 1
            else:
                # Regular line or end of section
                if line.strip():
                    result_lines.append(line)
                i += 1
        
        return '\n'.join(result_lines)
    
    def apply_diff_to_content(self, original_content: str, diff_content: str) -> str:
        """Apply a unified diff to existing content."""
        # This is a simplified approach - in practice, you'd want more robust diff application
        # For now, we'll use the LLM-generated content as-is since it should be complete
        
        # Parse the diff to extract the new content
        changes = self.parse_unified_diff(diff_content)
        
        # For simplicity, if we have changes, use the first one
        # In a real implementation, you'd need to match the file path
        if changes:
            return list(changes.values())[0]
        
        return original_content
    
    def extract_file_changes_from_diff(self, diff_content: str) -> Dict[str, str]:
        """Extract file changes from a unified diff."""
        # This is a more robust approach that reconstructs files from diffs
        changes = {}
        
        # Split by file boundaries
        file_sections = re.split(r'^(?=--- )', diff_content, flags=re.MULTILINE)
        
        for section in file_sections:
            if not section.strip():
                continue
            
            # Extract file path
            file_path = self._extract_file_path(section)
            if not file_path:
                continue
            
            # Check if this is a new file or modification
            if '--- /dev/null' in section:
                # New file
                new_content = self._extract_new_file_content(section)
                changes[file_path] = new_content
            else:
                # Modified file - we'll need the original content to apply changes
                # For now, we'll extract what we can from the diff
                modified_content = self._extract_modified_content(section)
                if modified_content:
                    changes[file_path] = modified_content
        
        return changes
    
    def _extract_file_path(self, section: str) -> Optional[str]:
        """Extract file path from diff section."""
        lines = section.split('\n')
        for line in lines:
            if line.startswith('+++ b/'):
                return line[6:]  # Remove '+++ b/'
            elif line.startswith('+++ '):
                path = line[4:]
                if path != '/dev/null':
                    return path
        return None
    
    def _extract_new_file_content(self, section: str) -> str:
        """Extract content for a new file."""
        lines = section.split('\n')
        content_lines = []
        
        in_content = False
        for line in lines:
            if line.startswith('@@'):
                in_content = True
                continue
            elif in_content and line.startswith('+'):
                content_lines.append(line[1:])  # Remove '+' prefix
        
        return '\n'.join(content_lines)
    
    def _extract_modified_content(self, section: str) -> Optional[str]:
        """Extract modified content from diff section."""
        lines = section.split('\n')
        content_lines = []
        
        in_content = False
        for line in lines:
            if line.startswith('@@'):
                in_content = True
                continue
            elif in_content:
                if line.startswith('+'):
                    content_lines.append(line[1:])  # Add new lines
                elif line.startswith(' '):
                    content_lines.append(line[1:])  # Add context lines
                # Skip lines starting with '-' (removed lines)
        
        return '\n'.join(content_lines) if content_lines else None
"""
LLM util for generating and reflecting on code diffs using OpenAI GPT.
"""

import os
import json
import logging
from typing import Dict, Any
from fastapi import HTTPException
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

async def generate_initial_diff(repo_structure: str, file_contents: str, prompt: str) -> str:
    """Generate initial diff using OpenAI GPT."""
    system_prompt = """You are an expert software developer. You will be given a repository structure, 
file contents, and a prompt describing changes to make. Generate a unified diff that represents 
the changes needed to fulfill the prompt.

Rules:
1. Generate a proper unified diff format
2. Only include files that actually need changes
3. Be precise and make minimal necessary changes
4. Include proper diff headers with file paths
5. Use standard unified diff format (--- and +++ headers, @@ chunk headers, - and + line prefixes)

Example format:
--- a/path/to/file.py
+++ b/path/to/file.py
@@ -1,5 +1,6 @@
 def function():
-    old_line
+    new_line
+    additional_line
     unchanged_line
"""

    user_prompt = f"""Repository structure:
{repo_structure}

File contents:
{file_contents}

Prompt: {prompt}

Generate a unified diff to implement the requested changes:"""

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"OpenAI API error in initial generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate initial diff: {str(e)}")

async def reflect_on_diff(original_diff: str, repo_structure: str, prompt: str) -> Dict[str, Any]:
    """Reflect on the generated diff and potentially improve it."""
    system_prompt = """You are an expert code reviewer. You will be given a unified diff, 
the original repository structure, and the prompt that generated it. Your job is to:

1. Analyze if the diff correctly implements the requested changes
2. Check for potential issues, bugs, or improvements
3. Determine if the diff should be modified

Respond with a JSON object containing:
- "needs_changes": boolean (true if the diff should be modified)
- "reasoning": string (explanation of your analysis)
- "improved_diff": string (only if needs_changes is true, provide the improved version)

If the diff is good as-is, set needs_changes to false."""

    user_prompt = f"""Original prompt: {prompt}

Repository structure:
{repo_structure}

Generated diff:
{original_diff}

Please analyze this diff and provide your reflection:"""

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=4000,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        reflection = json.loads(response.choices[0].message.content)
        return reflection
    except Exception as e:
        logger.error(f"OpenAI API error in reflection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reflect on diff: {str(e)}")
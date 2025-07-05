import logging
from fastapi import FastAPI
from models import DiffRequest, DiffResponse
from diff_generator import generate_diff

app = FastAPI(
    title="Repo-Manager",
    description="Generate unified diffs for Github Repositories using LLM reflection",
    version="0.1.0",
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Server is running"}


@app.post("/command", response_model=DiffResponse)
async def run_command(request: DiffRequest):
    """Generate a unified diff for the given repository and prompt."""
    return await generate_diff(request)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Repo Diff Generator API",
        "version": "1.0.0",
        "description": "Generate unified diffs for GitHub repositories using LLM reflection",
        "endpoints": {
            "POST /generate-diff": "Generate a unified diff for a GitHub repository",
            "GET /health": "Health check endpoint",
            "GET /docs": "OpenAPI documentation"
        }
    }
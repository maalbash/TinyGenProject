## How It Works

1. **Clone Repository:** Downloads the GitHub repo to temporary directory
2. **Analyze Structure:** Extracts file structure and key file contents
3. **Generate Initial Diff:** Uses GPT-4o-mini to create unified diff
4. **Reflection Step:** Second LLM call to review and potentially improve the diff
5. **Create Branch:** Creates a new feature branch in the repository
6. **Apply Changes:** Parses diff and applies changes to files via GitHub API
7. **Create Pull Request:** Opens a PR with# Repo Diff Generator API - Docker Setup Guide

## Quick Setup (Docker - Recommended)

1. **Create the project directory:**
   ```bash
   mkdir repo-diff-api
   cd repo-diff-api
   ```

2. **Save all the files:**
   - `main.py` (main FastAPI app)
   - `models.py` (Pydantic models)
   - `repo_handler.py` (repository utilities)
   - `llm_service.py` (OpenAI integration)
   - `diff_service.py` (core diff generation)
   - `requirements.txt`
   - `Dockerfile`
   - `docker-compose.yml`
   - `.env.example`

3. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys:
   # OPENAI_API_KEY=your-openai-api-key-here
   # GITHUB_TOKEN=your-github-token-here
   ```

4. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

The API will be available at `http://localhost:8000`

## Alternative Docker Commands

**Build and run manually:**
```bash
# Build the image
docker build -t repo-diff-api .

# Run the container
docker run -p 8000:8000 -e OPENAI_API_KEY="your-api-key-here" repo-diff-api
```

**Run in background:**
```bash
docker-compose up -d --build
```

**View logs:**
```bash
docker-compose logs -f
```

**Stop the service:**
```bash
docker-compose down
```

## Traditional Setup (Without Docker)

If you prefer not to use Docker:

1. **Set up virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Set your API keys:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   export GITHUB_TOKEN="your-github-token-here"
   ```

3. **Run the server:**
   ```bash
   python main.py
   ```

## Quick Cloud Deployment Options

### Option 1: Railway (Recommended - Easy)

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and deploy:**
   ```bash
   railway login
   railway create repo-diff-api
   railway up
   ```

3. **Set environment variable:**
   ```bash
   railway variables set OPENAI_API_KEY=your-api-key-here
   ```

### Option 2: Render

1. **Create a new Web Service on Render.com**
2. **Connect your GitHub repository**
3. **Use these settings:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add Environment Variable: `OPENAI_API_KEY`

### Option 3: Heroku

1. **Create Heroku app:**
   ```bash
   heroku create your-app-name
   heroku config:set OPENAI_API_KEY=your-api-key-here
   git push heroku main
   ```

2. **Create Procfile:**
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

### Option 4: DigitalOcean App Platform

1. **Create new app from GitHub**
2. **Configure:**
   - Source: Your repository
   - Build Command: `pip install -r requirements.txt`
   - Run Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables: `OPENAI_API_KEY`

## Testing the API

### Using curl:
```bash
curl -X POST "http://your-domain.com/generate-diff" \
  -H "Content-Type: application/json" \
  -d '{
    "repoUrl": "https://github.com/user/repo",
    "prompt": "Add error handling to the main function"
  }'
```

### Using Python requests:
```python
import requests

response = requests.post(
    "http://your-domain.com/generate-diff",
    json={
        "repoUrl": "https://github.com/user/repo",
        "prompt": "Add error handling to the main function"
    }
)

print(response.json())
```

## API Endpoints

- `POST /generate-diff` - Generate unified diff
- `GET /health` - Health check
- `GET /docs` - OpenAPI documentation
- `GET /` - API information

## Environment Variables

- `OPENAI_API_KEY` - Required: Your OpenAI API key
- `GITHUB_TOKEN` - Required: GitHub personal access token with repository write permissions

## GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with these scopes:
   - `repo` (Full control of private repositories)
   - `workflow` (Update GitHub Action workflows)
3. Copy the token and add it to your environment variables


## How It Works

1. **Clone Repository:** Downloads the GitHub repo to temporary directory
2. **Analyze Structure:** Extracts file structure and key file contents
3. **Generate Initial Diff:** Uses GPT-4o-mini to create unified diff
4. **Reflection Step:** Second LLM call to review and potentially improve the diff
5. **Return Result:** Provides final diff with reflection metadata

## Security Notes

- Only works with public GitHub repositories
- Temporary directories are cleaned up after each request
- No persistent storage of repository data
- API keys are handled securely through environment variables

## Troubleshooting

**Common Issues:**
- **Repository access errors:** Ensure the GitHub URL is correct and public
- **OpenAI API errors:** Check your API key and rate limits
- **Large repositories:** The API limits file reading to prevent timeouts

**Logs:** Check application logs for detailed error information
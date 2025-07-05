# TinyGen Project

A simple AI powered application to generate repository diffs with FastAPI, using OpenAI API to perform the actions, and is backed by supabase DB.

## How It Works

```bash
curl -X POST "http://your-domain.com/generate-diff" \
 -H "Content-Type: application/json" \
 -d '{
   "repoUrl": "https://github.com/user/repo",
   "prompt": "Add a new section to the README explaining how to contribute to the project",
   "enableReflection": false
 }'
```
The service then does the following:

1. **Clones Repository:** Downloads the GitHub repo to temporary directory
2. **Analyze Structure:** Extracts file structure and key file contents
3. **Generate Initial Diff:** Uses GPT-4o-mini to create unified diff
4. **Reflection Step:** Second LLM call in case enableReflection is true to review and potentially improve the diff
5. **Create Branch:** Creates a new feature branch in the repository
6. **Apply Changes:** Parses diff and applies changes to files via GitHub API
7. **Create Pull Request:** Opens a PR with# Repo Diff Generator API 

## Quick Setup (Docker)

1. **Clone the project locally:**
   ```bash
   git clone https://github.com/maalbash/TinyGenProject path/to/tinygen
   cd path/to/tinygen
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys, or add them to env in your machine using export command:
   # OPENAI_API_KEY=your-openai-api-key-here
   # GITHUB_TOKEN=your-github-token-here
   # SUPABASE_URL=your-supabase-url-here
   # SUPABASE_ANON_KEY=your-supabase-anon-key-here
   ```

4. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

The API will be available at `http://localhost:8000`

## Stop the service

```bash
docker-compose down
```

## API Endpoints

- `POST /generate-diff` - Generate unified diff
- `GET /health` - Health check
- `GET /` - API information

## Environment Variables

- `OPENAI_API_KEY` - Required: Your OpenAI API key
- `GITHUB_TOKEN` - Required: GitHub personal access token with repository write permissions
- `SUPABASE_URL` - Required: Url for the supabase instance used to store the inputs/outputs
- `SUPABASE_ANON_KEY` - Required: public anon key to use to access the db tables

## Security Notes

- Only works with public GitHub repositories
- Temporary directories are cleaned up after each request
- API keys are handled securely through environment variables
- supabase anon key can be replaced with a secret key, if the instance has row level security

## Troubleshooting

**Common Issues:**
- **Repository access errors:** Ensure the GitHub URL is correct and public
- **OpenAI API errors:** Check your API key and rate limits
- **Large repositories:** The API limits file reading to prevent timeouts

**Logs:** Check application logs for detailed error information
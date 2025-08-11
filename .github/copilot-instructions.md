# Trailarr Development Instructions

**ALWAYS follow these instructions first and only fallback to additional search and context gathering if the information here is incomplete or found to be in error.**

Trailarr is a Dockerized application for downloading and managing trailers for Radarr and Sonarr media libraries. It uses a Python FastAPI backend, Angular frontend, and SQLite database with Alembic migrations.

## Working Effectively

### Initial Setup Commands (NEVER CANCEL - Total setup time: ~3-4 minutes)
Execute these commands in order to set up the development environment:

```bash
# Backend setup - NEVER CANCEL: Takes 65 seconds. Set timeout to 2+ minutes.
cd backend
pip install -r requirements.txt

# Frontend setup - NEVER CANCEL: Takes 90 seconds. Set timeout to 3+ minutes.  
cd ../frontend
npm install

# Testing dependencies for backend - Takes 30 seconds
cd ../backend
pip install -r ../.devcontainer/requirements/testing.txt
```

### Build Commands (Validated and Working)

**Frontend Build - NEVER CANCEL: Takes 10 seconds. Set timeout to 30+ seconds.**
```bash
cd frontend
npm run build
```

**Docker Build - NEVER CANCEL: Takes 15-30 minutes normally. Set timeout to 60+ minutes.**
```bash
# Note: May fail in CI environments due to SSL certificate issues with PyPI
docker build --tag trailarr:latest .
```

### Test Commands (Validated and Working)

**Backend Tests - NEVER CANCEL: Takes 3 seconds. Set timeout to 60+ seconds.**
```bash
cd backend
PYTHONPATH=$(pwd) python -m pytest tests/ -v
# Result: 74 tests pass successfully
```

**Frontend Tests - NEVER CANCEL: Takes 13 seconds. Set timeout to 60+ seconds.**
```bash
cd frontend  
npm run test
# Note: Some tests may fail due to missing mocks, but framework works correctly
```

### Development Server Commands

**FastAPI Backend Server (for development)**
```bash
cd backend
PYTHONPATH=$(pwd) APP_DATA_DIR=/tmp/trailarr-config uvicorn main:trailarr_api --host 0.0.0.0 --port 7888
# Note: Requires database setup first - see Database Setup section
```

**Angular Frontend Development Server**
```bash
cd frontend
npm run start
# Runs on http://localhost:4200
```

## Database Setup

The application requires database initialization before running:

```bash
# Create config directory
mkdir -p /tmp/trailarr-config

# Set environment variables
export APP_DATA_DIR=/tmp/trailarr-config
export PYTHONPATH=$(pwd)/backend

# Run database migrations
cd backend
alembic upgrade head
```

**Note:** Database setup may require additional configuration files and environment setup that are typically handled by the Docker container.

## Validation Scenarios

**ALWAYS test these scenarios after making changes:**

1. **Backend API functionality:** Start the FastAPI server and verify it responds on port 7888
2. **Frontend build:** Run `npm run build` and verify the build completes without errors
3. **Test suites:** Run both backend and frontend tests to ensure no regressions
4. **Docker build:** If making changes that affect dependencies, test the Docker build process

## Common Tasks and File Locations

### Key Project Structure
```
/backend          - Python FastAPI application
  /api           - API route definitions  
  /config        - Configuration and settings
  /core          - Core business logic
  /alembic       - Database migrations
  /tests         - Backend test suite
  main.py        - FastAPI app entry point

/frontend        - Angular application
  /src/app       - Angular components and services
  /generated-sources - Auto-generated API client from OpenAPI
  package.json   - npm dependencies and scripts

/scripts         - Shell scripts for setup and deployment
/docs           - Markdown documentation  
/.vscode        - VSCode tasks and configuration
```

### Important Files to Check After Changes
- **API Changes:** Always check `backend/export_openapi.py` and regenerate frontend API client
- **Database Changes:** Check `backend/alembic/` for migrations
- **Build Changes:** Check `Dockerfile` and frontend `package.json`
- **Configuration:** Check `.vscode/tasks.json` for development commands

### Environment Variables
```bash
APP_DATA_DIR=/path/to/config     # Required - config and database location  
PYTHONPATH=/path/to/backend      # Required for backend development
TESTING=True                     # Optional - enables testing mode
LOG_LEVEL=Info                   # Optional - logging level
```

### VSCode Development Tasks
Use these VSCode tasks (defined in `.vscode/tasks.json`):
- **Frontend build** - Builds Angular application 
- **Fastapi run** - Starts FastAPI development server
- **Generate OpenAPI Files** - Updates API client code
- **Run FastAPI with startup script** - Full application startup

## Build Timing and Expectations

| Command | Expected Time | Timeout Recommendation |
|---------|---------------|-------------------------|
| Backend pip install | 65 seconds | 2+ minutes |
| Frontend npm install | 90 seconds | 3+ minutes |
| Frontend build | 10 seconds | 30+ seconds |
| Backend tests | 3 seconds | 60+ seconds |
| Frontend tests | 13 seconds | 60+ seconds |
| Docker build | 15-30 minutes | 60+ minutes |

**CRITICAL:** NEVER CANCEL long-running commands. All builds and tests must complete fully.

## Known Issues and Limitations

1. **Docker builds may fail** in CI environments due to SSL certificate issues with PyPI
2. **Application startup requires database setup** - cannot run FastAPI server without proper database configuration
3. **Some frontend tests fail** due to missing Angular testing mocks, but test infrastructure works
4. **Development requires manual environment setup** - the application is designed primarily for Docker deployment
5. **Database initialization is complex** - requires Alembic migrations and proper file permissions

## Key Technologies and Architecture

- **Backend:** Python 3.13, FastAPI, SQLModel, Alembic, SQLite
- **Frontend:** Angular 20, TypeScript, Jest testing
- **Documentation:** Mkdocs Material, Markdown files
- **Testing:** Pytest for backend, Jest for frontend
- **Media Processing:** ffmpeg, yt-dlp
- **Containerization:** Docker with multi-stage builds

## Coding Conventions

- **Python:** PEP-8, Black formatter, type hints, specific exceptions, log errors where caught
- **Angular:** Angular Style Guide, standalone components, Signals for reactivity, SCSS for styles
- **Commits:** Clear, descriptive messages; follow SemVer for versioning
- Add appropriate comments and docstrings for clarity
- Use type annotations for better code understanding and IDE support

## Troubleshooting

**Backend won't start:** Ensure APP_DATA_DIR is set and database file exists
**Frontend build errors:** Run `npm install` to ensure all dependencies are installed  
**Test failures:** Check that all testing dependencies are installed
**Import errors:** Verify PYTHONPATH is set correctly for backend modules
**Docker build fails:** May be environment-specific SSL issues, try local Docker build

## Validation Checklist

Before committing changes:
- [ ] Backend tests pass: `pytest tests/`
- [ ] Frontend builds: `npm run build` 
- [ ] No linting errors: Check VSCode problems panel
- [ ] API client updated if backend API changed
- [ ] Documentation updated if public interfaces changed

Always run the complete test suite and build process to ensure your changes don't break existing functionality.

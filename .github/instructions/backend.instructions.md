---
description: "Backend development instructions for Python FastAPI application"
applyTo: "**/*.py"
---

# Backend Development Instructions

This document provides comprehensive instructions for developing and maintaining the Trailarr backend. **Follow these guidelines alongside the Python instructions (`python.instructions.md`) and main copilot instructions (`copilot-instructions.md`).**

## Architecture Overview

The backend is a **Python 3.13 FastAPI application** using:

- **SQLModel** (SQLAlchemy + Pydantic) for ORM and data validation
- **Alembic** for database migrations
- **SQLite** with WAL mode for persistence
- **APScheduler** for background task scheduling

### High-Level Directory Structure

```
backend/
├── main.py                    # FastAPI app entry point, lifespan, middleware setup
├── app_logger.py              # Custom logging adapter (ModuleLogger)
├── exceptions.py              # Custom exception classes
├── export_openapi.py          # OpenAPI schema generation for frontend
├── alembic.ini                # Alembic configuration
├── pyproject.toml             # Python project dependencies (uv)
├── uv.lock                    # Locked dependency versions
│
├── api/                       # API layer (HTTP routes)
│   ├── utils.py               # API utilities (docstring formatting)
│   └── v1/                    # API version 1
│       ├── routes.py          # Main router aggregation
│       ├── authentication.py  # Auth dependencies (API key validation)
│       ├── models.py          # Pydantic models for API requests/responses
│       ├── websockets.py      # WebSocket connection manager
│       └── [resource].py      # Resource-specific route handlers
│
├── config/                    # Application configuration
|   ├── logs/                  # Logging to database (model, engine, config, manager)
│   ├── settings.py            # App settings (environment variables)
│   ├── app_logger_opts.py     # Logger level configuration
│   ├── logger_config.json     # Logging configuration
│   ├── logging_context.py     # Logging context utilities
│   └── timing_middleware.py   # Request timing middleware
│
├── core/                      # Core business logic
│   ├── files_handler.py       # File operations handler (needs to be break down and move to files package)
│   ├── base/                  # Shared base components
│   │   ├── database/          # Database layer
│   │   │   ├── models/        # SQLModel table definitions
│   │   │   ├── manager/       # CRUD operations per model
│   │   │   └── utils/         # DB engine, session management
│   │   ├── arr_manager/       # Base Arr API client
│   │   ├── connection_manager.py # Arr Connection manager (refresh data)
│   │   └── utils/             # Shared utilities
│   ├── radarr/                # Radarr-specific logic
│   ├── sonarr/                # Sonarr-specific logic
│   ├── download/              # download logic (images, trailers)
│   ├── files/                 # File management
│   ├── tasks/                 # Background task definitions
│   └── updates/               # Update checking logic
│
├── alembic/                   # Database migrations
│   ├── env.py                 # Alembic environment config
│   ├── script.py.mako         # Migration template
│   └── versions/              # Migration files (timestamp prefixed)
│
└── tests/                     # Test suite
    ├── conftest.py            # Pytest fixtures and configuration
    ├── api/                   # API route tests
    ├── config/                # Configuration tests
    ├── core/                  # Core logic tests
    └── services/              # Service tests
```

## Core Patterns

### 1. Database Layer Pattern

The database layer follows a **Model → Manager → API** pattern:

#### Models (`core/base/database/models/`)

Define SQLModel classes with clear separation:

```python
# base.py - Base model with common functionality
class AppSQLModel(SQLModel):
    """Base class with timezone handling utilities."""

# [resource].py - Resource-specific models
class MediaBase(AppSQLModel):
    """Base fields - DO NOT USE DIRECTLY."""
    # Shared fields for Create, Read, Update

class Media(MediaBase, table=True):
    """Database table model - DO NOT USE DIRECTLY."""
    id: int | None = Field(default=None, primary_key=True)
    # Relationships, computed fields
    # Should only be used in manager

class MediaCreate(MediaBase):
    """Model for creating new records."""

class MediaRead(MediaBase):
    """Model for reading records (includes id, timestamps)."""
    id: int
    added_at: datetime

class MediaUpdate(SQLModel):
    """Model for partial updates (all fields optional)."""
    title: str | None = None
```

#### Managers (`core/base/database/manager/`)

- Always fetch db model of resource and return read model, db model should never leave manager
- Should be short operations to prevent db lockup
- Only create functions that are required. For example, if delete operation is not used in app logic, do not expose it.
- Only expose functions that are required
- App is using SQLite database with `PRAGMA foreign_keys=ON` so no need to add logic for deleting related objects.

Organize CRUD operations in subfolders:

```python
# manager/media/__init__.py - Export all functions
from .create import create_or_update_bulk
from .read import read, read_all, read_all_raw
from .update import update_monitoring
from .delete import delete

__all__ = ["create_or_update_bulk", "read", "read_all", ...]
```

Each operation file uses the session decorator:

```python
from core.base.database.utils.engine import manage_session

@manage_session
def read(
    item_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> ItemRead:
    """Read item by ID. \n
    Args:
        item_id (int): The item ID.
        _session (optional): Database session (auto-injected). \n
    Returns:
        ItemRead: The item data. \n
    Raises:
        ItemNotFoundError: If item doesn't exist.
    """
    statement = select(Item).where(Item.id == item_id)
    item = _session.exec(statement).first()
    if not item:
        raise ItemNotFoundError("Item", item_id)
    return ItemRead.model_validate(item)
```

### 2. API Route Pattern

Routes are organized by resource in `api/v1/`:

```python
from fastapi import APIRouter, HTTPException, status
from api.v1.models import ErrorResponse
from app_logger import ModuleLogger
import core.base.database.manager.resource as resource_manager
from core.base.database.models.resource import ResourceCreate, ResourceRead

logger = ModuleLogger("ResourceAPI")

resource_router = APIRouter(prefix="/resource", tags=["Resource"])

@resource_router.get("/")
async def get_all_resources() -> list[ResourceRead]:
    """Get all resources. \n
    Returns:
        list[ResourceRead]: List of resource objects.
    """
    return resource_manager.read_all()

@resource_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Validation error",
        },
    },
)
async def create_resource(resource: ResourceCreate) -> ResourceRead:
    """Create a new resource. \n
    Args:
        resource (ResourceCreate): Resource data. \n
    Returns:
        ResourceRead: Created resource. \n
    Raises:
        HTTPException: If validation fails.
    """
    try:
        return resource_manager.create(resource)
    except Exception as e:
        logger.error(f"Failed to create resource: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
```

**Register new routers in `api/v1/routes.py`:**

```python
from api.v1.resource import resource_router

authenticated_router.include_router(resource_router)
```

### 3. Logging Pattern

Use `ModuleLogger` for consistent, prefixed logging:

```python
from app_logger import ModuleLogger

logger = ModuleLogger("ModuleName")

# Standard levels
logger.debug("Detailed diagnostic information")
logger.info("General operational messages")
logger.warning("Warning about potential issues")
logger.error("Error occurred but handled")

# Include media_id for frontend linking
logger.info(f"Processing trailer download for '{media.title}' [{media.id}]")
logger.error(f"Download failed for '{media.title}' [{media.id}]: {error}")
```

### 4. Exception Handling Pattern

- Log exceptions where caught, not when they are raised. Include exception details in the log if user needs to be informed.

Define custom exceptions in `exceptions.py`:

```python
class ItemNotFoundError(Exception):
    """Raised when an Item is not found in the database."""

    def __init__(self, model_name: str, id: int) -> None:
        message = f"{model_name} with id {id} not found"
        super().__init__(message)
```

Handle exceptions at the API layer:

```python
@router.get("/{item_id}")
async def get_item(item_id: int) -> ItemRead:
    try:
        return item_manager.read(item_id)
    except ItemNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error reading item {item_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal error")
```

### 5. Background Tasks Pattern

Tasks are using `apscheduler`, defined in `core/tasks/` and scheduled in `main.py`:

```python
# core/tasks/my_task.py
from app_logger import ModuleLogger

logger = ModuleLogger("MyTask")

def my_background_job():
    """Execute background task."""
    logger.info("Starting background job")
    # ... task logic
    logger.info("Background job completed")

# core/tasks/schedules.py
from core.tasks import scheduler
from core.tasks.my_task import my_background_job

def schedule_all_tasks():
    scheduler.add_job(
        my_background_job,
        "interval",
        hours=1,
        id="my_background_job",
        replace_existing=True,
    )
```

## Database Migrations

**All Alembic commands must be run from the `backend/` directory.**

### Running Migrations

```bash
# Apply all pending migrations
cd backend
uv run alembic upgrade head

# Check current migration status
uv run alembic current

# View migration history
uv run alembic history
```

### Creating a New Migration

1. **Modify the SQLModel** in `core/base/database/models/`

2. **Generate migration** using the Alembic CLI (preferred):

```bash
cd backend
uv run alembic revision --autogenerate -m "Add description of changes"
```

3. **Review and edit** the generated file in `alembic/versions/`

    - Verify auto-generated operations are correct
    - Add data migrations if needed
    - Ensure `upgrade()` and `downgrade()` are properly implemented

4. **Test the migration**:

    ```bash
    cd backend
    uv run alembic upgrade head
    ```

5. **Migration file naming**: `YYYYMMDD_HHMM-{revision}_description.py`

### Migration Best Practices

```python
"""Add new_column to media

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2025-01-09 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from app_logger import ModuleLogger

revision: str = "abc123def456"
down_revision: str = "previous_revision"

logger = ModuleLogger("AlembicMigrations")

def upgrade() -> None:
    # Disable foreign keys for SQLite migrations
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("new_column", sa.String(), server_default="", nullable=False)
        )

    # Re-enable foreign keys
    op.execute("PRAGMA foreign_keys=ON")

def downgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("media", schema=None) as batch_op:
        batch_op.drop_column("new_column")

    op.execute("PRAGMA foreign_keys=ON")
```

## Testing

- Use same file structure as original file within `tests/` for related tests.
- Ensure tests are added/updated for critical edge cases. For example, if we are testing a method that processes all media items for trailer downloads, and we need to skip downloading for media with `folder_path` not set, missing from disk, or trailer already downloaded - we need to test all 3 of these edge cases.

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures, temp DB setup
├── api/                 # API endpoint tests
├── config/              # Configuration tests
├── core/
│   ├── base/
│   │   └── database/    # Database operation tests
│   └── download/        # Download logic tests
└── services/            # Service integration tests
```

### Writing Tests

```python
import pytest
from core.base.database.manager import resource as resource_manager
from core.base.database.models.resource import ResourceCreate

class TestResourceManager:
    """Tests for resource manager operations."""

    def test_create_resource(self):
        """Test creating a new resource."""
        resource_data = ResourceCreate(name="Test", value=123)
        result = resource_manager.create(resource_data)

        assert result.id is not None
        assert result.name == "Test"

    def test_read_nonexistent_resource(self):
        """Test reading a resource that doesn't exist."""
        from exceptions import ItemNotFoundError

        with pytest.raises(ItemNotFoundError):
            resource_manager.read(99999)
```

### Running Tests

```bash
cd backend
uv run python -m pytest tests/ -v

# With coverage
uv run python -m pytest --cov=. --cov-report=html
```

## Common Tasks

### Adding a New API Endpoint

1. **Create/update models** in `core/base/database/models/[resource].py`
2. **Create/update manager** functions in `core/base/database/manager/[resource]/`
3. **Add route handler** in `api/v1/[resource].py`
4. **Register router** in `api/v1/routes.py` (if new file)
5. **Add tests** in `tests/api/` and `tests/core/`
6. **Regenerate OpenAPI** - Run VSCode task "Generate OpenAPI Files"
7. **Update frontend API client** - Run `npm run openapi` in frontend

### Adding a New Database Model

1. **Create model file** in `core/base/database/models/[model].py`
2. **Export from** `core/base/database/models/__init__.py`
3. **Create manager folder** `core/base/database/manager/[model]/`
4. **Add CRUD operations** (create.py, read.py, update.py, delete.py)
5. **Export from manager** `__init__.py`
6. **Create migration**:
    ```bash
    cd backend
    uv run alembic revision --autogenerate -m "Add [model] table"
    ```
7. **Add tests** for manager

### Adding a New Background Task

1. **Create task file** in `core/tasks/[task_name].py`
2. **Add schedule** in `core/tasks/schedules.py`
3. **Add tests** in `tests/core/tasks/`

## Documentation Requirements

When making backend changes, update the following:

### Code Documentation

- Add docstrings following Google style (see `python.instructions.md`)
- Include `Args:`, `Returns:`, `Raises:` sections
- Ensure proper indentation is used for proper OpenAPI rendering

### API Documentation

1. **Regenerate OpenAPI schema**: Run VSCode task "Generate OpenAPI Files"
2. **Update API client**: Run `npm run openapi` in frontend directory

### User Documentation

Update relevant files in `/docs/` when:

- Adding new API endpoints → Update `docs/references/api-docs/`
- Changing settings → Update `docs/user-guide/settings/`
- Adding new features → Update appropriate user guide section
- Changing behavior → Update `docs/troubleshooting/` if applicable

### Release Notes

For significant changes, add entry to `docs/release-notes/[year].md`

## Environment Variables

```python
# Required
APP_DATA_DIR: str       # Config and database location (/config in Docker)

# Optional
TESTING: bool = False   # Enable testing mode (in-memory DB)
LOG_LEVEL: str = "Info" # Logging level (Debug, Info, Warning, Error)
TZ: str = "UTC"         # Timezone
```

## Code Quality Checklist

Before committing backend changes:

- [ ] Code follows PEP 8, black formatter and project conventions
- [ ] Type hints added for all function parameters and returns
- [ ] Docstrings added/updated with Google style format
- [ ] Custom exceptions used instead of generic ones
- [ ] Logging added at appropriate levels with `'{media.title}' [{media_id}]` where applicable
- [ ] Tests written/updated for new functionality
- [ ] All tests pass: `uv run python -m pytest tests/ -v`
- [ ] Database migration created if model changed
- [ ] OpenAPI schema regenerated if API changed
- [ ] Frontend API client regenerated if API changed
- [ ] Documentation updated for user-facing changes

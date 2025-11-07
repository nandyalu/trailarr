# Trailer Download Tracking Implementation Task

## Objective
Implement a trailer download tracking system for the Trailarr application that records comprehensive metadata about downloaded trailers in a database, including video/audio stream information, allowing users to view detailed download history for each media item.

## Prerequisites
- Start from the main branch (commit: f1b22b35030da9a142415d8d623c33b14c6a0001 or latest)
- Python 3.13 is used, so use modern type hints (`list`, `dict`, not `List`, `Dict`)
- Follow existing code patterns in the repository
- Use SQLModel for database models
- Use Alembic for database migrations

## Implementation Steps

### 1. Create Download Model (`backend/core/base/database/models/download.py`)

Create a new file with the following structure:

```python
from __future__ import annotations
from datetime import datetime, timezone

from sqlmodel import Field, JSON, Column
from sqlalchemy import String

from core.base.database.models.base import AppSQLModel


def get_current_time():
    return datetime.now(timezone.utc)


class DownloadBase(AppSQLModel):
    """
    Base model for Download.\n
    Note: \n
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨 \n
    👉Use :class:`Download` for working with database.👈 \n
    👉Use :class:`DownloadCreate` to create/update downloads.👈 \n
    👉Use :class:`DownloadRead` to read the data.👈
    """
    
    path: str
    file_name: str
    size: int
    resolution: str  # e.g., "1080p", "2160p"
    file_format: str  # e.g., "mp4", "mkv", "webm"
    video_format: str  # e.g., "h264", "h265", "av1"
    audio_format: str  # e.g., "aac", "ac3", "opus"
    audio_language: str | None = None  # e.g., "eng", "tel"
    subtitle_format: str | None = None  # e.g., "srt", "ass", or None
    subtitle_language: str | None = None  # e.g., "eng", or None
    duration: int = 0  # Duration in seconds
    youtube_id: str
    file_exists: bool = True
    profile_name: str  # Name of the TrailerProfile used
    added_at: datetime  # When trailer was downloaded (from file)
    updated_at: datetime  # When file was last modified (from file)


class Download(DownloadBase, table=True):
    """
    Database model for Download.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    👉Use :class:`DownloadCreate` to create/update downloads.👈 \n
    👉Use :class:`DownloadRead` to read the data.👈
    """
    
    id: int | None = Field(default=None, primary_key=True)
    media_id: int = Field(foreign_key="media.id", ondelete="CASCADE")


class DownloadCreate(DownloadBase):
    """
    Model for creating/updating Download.
    """
    
    id: int | None = None
    media_id: int


class DownloadRead(DownloadBase):
    """
    Model for reading Download.
    """
    
    id: int
    media_id: int


class DownloadUpdate(AppSQLModel):
    """
    Model for updating Download.
    Only updatable fields should be included.
    """
    
    file_exists: bool | None = None
    updated_at: datetime | None = None
```

**Key Points:**
- Keep it simple - no bidirectional relationships with Media model
- Only `media_id` as foreign key with CASCADE delete
- Use Python 3.13 type hints (`int | None`, not `Optional[int]`)
- Includes comprehensive metadata: resolution, codecs, languages, duration
- `profile_name` stores the TrailerProfile name used for download
- `added_at` and `updated_at` extracted from file metadata

### 2. Update VideoInfo Model (`backend/core/download/video_analysis.py`)

**Update the VideoInfo class to include additional fields:**

```python
class VideoInfo(BaseModel):
    name: str
    format_name: str
    duration_seconds: int = 0
    duration: str = "0:00:00"
    size: int = 0
    bitrate: str = "0 bps"
    streams: list[StreamInfo]
    youtube_id: str | None = None  # ADD THIS
    created_at: datetime | None = None  # ADD THIS - file creation time
    updated_at: datetime | None = None  # ADD THIS - file modification time
```

**Update `get_media_info` function to extract these fields:**

In the `entries_required` variable, add format_tags:
```python
entries_required = (
    "format=format_name,duration,size,bit_rate :"
    " format_tags=comment,description,synopsis,YouTube,youtube_id,creation_time :"  # ADD THESE
    " stream=index,codec_type,codec_name,coded_height,coded_width,channels,sample_rate"
    " : stream_tags=language,duration,name"
)
```

After parsing format info and before creating VideoInfo object, add extraction:
```python
import os
from pathlib import Path

format: dict[str, str] = info.get("format", {})
format_tags: dict[str, str] = format.get("tags", {})

# Extract YouTube ID from format tags
youtube_id = None
for tag_key in ["youtube_id", "YouTube", "comment", "description", "synopsis"]:
    tag_value = format_tags.get(tag_key, "")
    if tag_value:
        # YouTube IDs are 11 characters long
        match = re.search(r'(?:v=|/)([A-Za-z0-9_-]{11})', tag_value)
        if match:
            youtube_id = match.group(1)
            break

# Get file timestamps
file_path_obj = Path(file_path)
file_stat = file_path_obj.stat()
created_at = datetime.fromtimestamp(file_stat.st_ctime, tz=timezone.utc)
updated_at = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)

# Alternatively, try to get creation_time from format tags
creation_time_str = format_tags.get("creation_time")
if creation_time_str:
    try:
        created_at = datetime.fromisoformat(creation_time_str.replace('Z', '+00:00'))
    except:
        pass  # Use file stat time if parsing fails

# Create VideoInfo object
video_info = VideoInfo(
    name=os.path.basename(file_path),
    format_name=str(format.get("format_name", "N/A")),
    duration_seconds=int(float(format.get("duration", "0"))),
    duration=convert_duration(format.get("duration", "0")),
    size=int(format.get("size", "0")),
    bitrate=convert_bitrate(format.get("bit_rate", "0")),
    streams=[],
    youtube_id=youtube_id,  # ADD THIS
    created_at=created_at,  # ADD THIS
    updated_at=updated_at,  # ADD THIS
)
```

### 3. Create Separate Database Manager for Downloads

Create a dedicated database manager structure for Download operations.

**File: `backend/core/base/database/manager/download/__init__.py`**

```python
from .base import DownloadDatabaseManager

__all__ = ["DownloadDatabaseManager"]
```

**File: `backend/core/base/database/manager/download/base.py`**

```python
from .create import DownloadCreateMixin
from .read import DownloadReadMixin
from .update import DownloadUpdateMixin
from .delete import DownloadDeleteMixin


class DownloadDatabaseManager(
    DownloadCreateMixin,
    DownloadReadMixin,
    DownloadUpdateMixin,
    DownloadDeleteMixin,
):
    """
    Database manager for CRUD operations on Download objects.\n
    Combines all download database operations from separate mixins.
    """
    
    __model_name = "Download"
```

**File: `backend/core/base/database/manager/download/create.py`**

```python
from sqlmodel import Session

from core.base.database.models.download import Download, DownloadCreate, DownloadRead
from core.base.database.utils.engine import manage_session
from app_logger import logger


class DownloadCreateMixin:
    """Mixin for create operations on Download objects."""
    
    @manage_session
    def create(
        self,
        download_create: DownloadCreate,
        *,
        _session: Session = None,  # type: ignore
    ) -> DownloadRead:
        """Create a new download record in the database.\n
        Args:
            download_create (DownloadCreate): The download object to create.\n
            _session (Session, Optional): A session to use for the database connection.\n
                Default is None, in which case a new session will be created.\n
        Returns:
            DownloadRead: The created download object.
        """
        try:
            db_download = Download.model_validate(download_create)
            _session.add(db_download)
            _session.commit()
            _session.refresh(db_download)
            return DownloadRead.model_validate(db_download)
        except Exception as e:
            logger.error(f"Error creating download: {e}")
            _session.rollback()
            raise
```

**File: `backend/core/base/database/manager/download/read.py`**

```python
from sqlmodel import Session, select

from core.base.database.models.download import Download, DownloadRead
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError
from app_logger import logger


class DownloadReadMixin:
    """Mixin for read operations on Download objects."""
    
    __model_name = "Download"
    
    @manage_session
    def read(
        self,
        download_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> DownloadRead:
        """Read a download by ID from the database.\n
        Args:
            download_id (int): The ID of the download to read.\n
            _session (Session, Optional): A session to use for the database connection.\n
        Returns:
            DownloadRead: The download object.
        Raises:
            ItemNotFoundError: If download not found.
        """
        db_download = _session.get(Download, download_id)
        if not db_download:
            raise ItemNotFoundError(self.__model_name, download_id)
        return DownloadRead.model_validate(db_download)
    
    @manage_session
    def read_all_for_media(
        self,
        media_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[DownloadRead]:
        """Get all downloads for a specific media item.\n
        Args:
            media_id (int): The ID of the media to get downloads for.\n
            _session (Session, Optional): A session to use for the database connection.\n
        Returns:
            list[DownloadRead]: List of download objects for the media item.
        """
        statement = select(Download).where(Download.media_id == media_id)
        downloads = _session.exec(statement).all()
        return [DownloadRead.model_validate(d) for d in downloads]
    
    @manage_session
    def read_all(
        self,
        *,
        _session: Session = None,  # type: ignore
    ) -> list[DownloadRead]:
        """Get all downloads from the database.\n
        Args:
            _session (Session, Optional): A session to use for the database connection.\n
        Returns:
            list[DownloadRead]: List of all download objects.
        """
        statement = select(Download)
        downloads = _session.exec(statement).all()
        return [DownloadRead.model_validate(d) for d in downloads]
```

**File: `backend/core/base/database/manager/download/update.py`**

```python
from datetime import datetime, timezone
from sqlmodel import Session

from core.base.database.models.download import Download, DownloadUpdate, DownloadRead
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError
from app_logger import logger


class DownloadUpdateMixin:
    """Mixin for update operations on Download objects."""
    
    __model_name = "Download"
    
    @manage_session
    def update(
        self,
        download_id: int,
        download_update: DownloadUpdate,
        *,
        _session: Session = None,  # type: ignore
    ) -> DownloadRead:
        """Update a download in the database.\n
        Args:
            download_id (int): The ID of the download to update.\n
            download_update (DownloadUpdate): The download update object.\n
            _session (Session, Optional): A session to use for the database connection.\n
        Returns:
            DownloadRead: The updated download object.
        Raises:
            ItemNotFoundError: If download not found.
        """
        db_download = _session.get(Download, download_id)
        if not db_download:
            raise ItemNotFoundError(self.__model_name, download_id)
        
        # Update only provided fields
        update_data = download_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_download, key, value)
        
        _session.add(db_download)
        _session.commit()
        _session.refresh(db_download)
        return DownloadRead.model_validate(db_download)
    
    @manage_session
    def mark_as_deleted(
        self,
        download_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> DownloadRead:
        """Mark a download as deleted (file no longer exists).\n
        Args:
            download_id (int): The ID of the download to mark as deleted.\n
            _session (Session, Optional): A session to use for the database connection.\n
        Returns:
            DownloadRead: The updated download object.
        Raises:
            ItemNotFoundError: If download not found.
        """
        update = DownloadUpdate(
            file_exists=False,
            updated_at=datetime.now(timezone.utc)
        )
        return self.update(download_id, update, _session=_session)
```

**File: `backend/core/base/database/manager/download/delete.py`**

```python
from sqlmodel import Session

from core.base.database.models.download import Download
from core.base.database.utils.engine import manage_session
from exceptions import ItemNotFoundError
from app_logger import logger


class DownloadDeleteMixin:
    """Mixin for delete operations on Download objects."""
    
    __model_name = "Download"
    
    @manage_session
    def delete(
        self,
        download_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> None:
        """Delete a download from the database.\n
        Args:
            download_id (int): The ID of the download to delete.\n
            _session (Session, Optional): A session to use for the database connection.\n
        Raises:
            ItemNotFoundError: If download not found.
        """
        db_download = _session.get(Download, download_id)
        if not db_download:
            raise ItemNotFoundError(self.__model_name, download_id)
        
        _session.delete(db_download)
        _session.commit()
    
    @manage_session
    def delete_all_for_media(
        self,
        media_id: int,
        *,
        _session: Session = None,  # type: ignore
    ) -> int:
        """Delete all downloads for a specific media item.\n
        Args:
            media_id (int): The ID of the media whose downloads to delete.\n
            _session (Session, Optional): A session to use for the database connection.\n
        Returns:
            int: Number of downloads deleted.
        """
        from sqlmodel import select
        
        statement = select(Download).where(Download.media_id == media_id)
        downloads = _session.exec(statement).all()
        count = len(downloads)
        
        for download in downloads:
            _session.delete(download)
        
        _session.commit()
        return count
```

### 4. Create Download Service (`backend/core/download/service.py`)

Create a service to record new trailer downloads with enhanced metadata extraction:

```python
import os
from datetime import datetime, timezone

from app_logger import ModuleLogger
from core.base.database.manager.download import DownloadDatabaseManager
from core.base.database.models.download import DownloadCreate
from core.download.video_analysis import get_media_info

logger = ModuleLogger("DownloadService")


def get_resolution_label(width: int, height: int) -> str:
    """Convert resolution dimensions to standard labels (e.g., 1080p, 2160p)."""
    if height >= 2160:
        return "2160p"  # 4K
    elif height >= 1440:
        return "1440p"  # 2K
    elif height >= 1080:
        return "1080p"  # Full HD
    elif height >= 720:
        return "720p"   # HD
    elif height >= 480:
        return "480p"   # SD
    else:
        return f"{height}p"


async def record_new_trailer_download(
    media_id: int,
    profile_name: str,
    file_path: str,
    youtube_video_id: str,
) -> None:
    """
    Records a new trailer download in the database with comprehensive metadata.

    Args:
        media_id (int): The ID of the media.
        profile_name (str): The name of the TrailerProfile used for download.
        file_path (str): The path to the downloaded file.
        youtube_video_id (str): The YouTube video ID of the trailer.
    """
    logger.info(f"Recording new trailer download for media {media_id}")
    try:
        # Get media info using ffprobe
        media_info = get_media_info(file_path)
        if not media_info:
            logger.error(f"Failed to get media info for {file_path}")
            return

        # Extract video stream info
        video_stream = next(
            (s for s in media_info.streams if s.codec_type == "video"), None
        )
        
        # Extract audio stream info (prefer first audio stream)
        audio_stream = next(
            (s for s in media_info.streams if s.codec_type == "audio"), None
        )
        
        # Extract subtitle stream info (if any)
        subtitle_stream = next(
            (s for s in media_info.streams if s.codec_type == "subtitle"), None
        )

        # Determine resolution label
        resolution = "unknown"
        if video_stream:
            resolution = get_resolution_label(
                video_stream.coded_width,
                video_stream.coded_height
            )

        # Create download record with comprehensive metadata
        download = DownloadCreate(
            path=file_path,
            file_name=os.path.basename(file_path),
            size=media_info.size,
            resolution=resolution,
            file_format=media_info.format_name.split(',')[0],  # Get primary format
            video_format=video_stream.codec_name if video_stream else "N/A",
            audio_format=audio_stream.codec_name if audio_stream else "N/A",
            audio_language=audio_stream.language if audio_stream and audio_stream.language else None,
            subtitle_format=subtitle_stream.codec_name if subtitle_stream else None,
            subtitle_language=subtitle_stream.language if subtitle_stream and subtitle_stream.language else None,
            duration=media_info.duration_seconds,
            youtube_id=youtube_video_id,
            file_exists=True,
            profile_name=profile_name,
            media_id=media_id,
            added_at=media_info.created_at or datetime.now(timezone.utc),
            updated_at=media_info.updated_at or datetime.now(timezone.utc),
        )

        # Save to database using dedicated download manager
        db_manager = DownloadDatabaseManager()
        db_manager.create(download)
        logger.info(f"Successfully recorded new trailer download for media {media_id}")

    except Exception as e:
        logger.error(
            f"Failed to record new trailer download for media {media_id}: {e}"
        )
```

**Key Changes from Original:**
- Uses `DownloadDatabaseManager` instead of `MediaDatabaseManager`
- Takes `profile_name` (string) instead of `profile_id` (int)
- Extracts resolution as standard label (1080p, 2160p, etc.)
- Extracts audio and subtitle language information
- Uses `created_at` and `updated_at` from VideoInfo
- More robust codec extraction from streams

### 5. Integrate Download Tracking in Trailer Download (`backend/core/download/trailer.py`)

**Add import at the top:**
```python
from core.download.service import record_new_trailer_download
```

**Update the `download_trailer` function:**

Find where `trailer_file.move_trailer_to_folder` is called (around line 115-120) and update:

```python
try:
    __update_media_status(media, MonitorStatus.DOWNLOADING)
    # Download the trailer and verify
    output_file = __download_and_verify_trailer(media, video_id, profile)
    # Move the trailer to the media folder (create subfolder if needed)
    final_file_path = trailer_file.move_trailer_to_folder(output_file, media, profile)  # CAPTURE RETURN VALUE
    __update_media_status(media, MonitorStatus.DOWNLOADED)
    
    # ADD THIS BLOCK - Record the download with profile name:
    await record_new_trailer_download(
        media_id=media.id,
        profile_name=profile.name,  # Use profile.name instead of profile.id
        file_path=final_file_path,
        youtube_video_id=video_id,
    )
    
    msg = (
        f"Trailer downloaded successfully for {media.title} [{media.id}]"
        f" from ({video_id})"
    )
    logger.info(msg)
    await websockets.ws_manager.broadcast(msg, "Success")
    return True
```

### 6. Create Alembic Migration

Generate a new migration file in `backend/alembic/versions/` with a timestamp like `20251107_HHMM-{revision_id}_add_download_model.py`:

```python
"""Add download model

Revision ID: {generate_unique_id}
Revises: b213e0443c1b
Create Date: {current_timestamp}

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from app_logger import ModuleLogger

# revision identifiers, used by Alembic.
revision: str = "{generate_unique_id}"  # Generate unique 12-char ID
down_revision: Union[str, None] = "b213e0443c1b"  # Latest migration in main
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    # Disable foreign keys temporarily for migrations
    op.execute("PRAGMA foreign_keys=OFF")

    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "download",
        sa.Column("path", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("file_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("resolution", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("file_format", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("video_format", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("audio_format", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("audio_language", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("subtitle_format", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("subtitle_language", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("youtube_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("file_exists", sa.Boolean(), nullable=False),
        sa.Column("profile_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("media_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["media_id"],
            ["media.id"],
            name=op.f("fk_download_media_id_media"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_download")),
    )
    # ### end Alembic commands ###

    # Re-enable foreign keys after migrations
    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    # Disable foreign keys temporarily for migrations
    op.execute("PRAGMA foreign_keys=OFF")

    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("download")
    # ### end Alembic commands ###

    # Re-enable foreign keys after migrations
    op.execute("PRAGMA foreign_keys=ON")
```

**Important:** 
- Set `down_revision` to `"b213e0443c1b"` (the latest migration in main branch)
- Generate a unique revision ID (12 random alphanumeric characters)
- Note the updated columns matching the new Download model structure

### 7. Testing

After implementation, test the migration:

```bash
cd backend
alembic upgrade head
```

The migration should run successfully without errors.

## Important Notes

1. **Keep It Simple:** No bidirectional relationships between Media and Download models
2. **CASCADE Delete:** The foreign key constraint ensures downloads are deleted when media is deleted
3. **Query Approach:** To get downloads for a media item, query directly: `session.query(Download).filter(Download.media_id == media_id).all()`
4. **Python 3.13:** Use modern type hints (`list`, `dict`, `int | None`)
5. **No model_validate Overrides:** Keep models simple without custom validation logic

## Code Style Guidelines

- Follow PEP 8
- Use type hints for all function parameters and return values
- Add docstrings to classes and functions
- Use descriptive variable names
- Keep functions focused on a single responsibility
- Handle exceptions appropriately with logging

## Expected Outcome

After implementation:
- New `download` table in database
- Downloads are automatically recorded when trailers are downloaded
- Each download contains metadata: resolution, codecs, duration, file size, etc.
- CASCADE delete ensures orphaned downloads are cleaned up
- Clean, maintainable code without complex relationships
- Separate database operations for better organization

## File Summary

### New Files to Create:
1. `backend/core/base/database/models/download.py` - Download model with comprehensive metadata
2. `backend/core/base/database/manager/download/__init__.py` - Download manager package init
3. `backend/core/base/database/manager/download/base.py` - Download manager base class
4. `backend/core/base/database/manager/download/create.py` - Create operations mixin
5. `backend/core/base/database/manager/download/read.py` - Read operations mixin
6. `backend/core/base/database/manager/download/update.py` - Update operations mixin
7. `backend/core/base/database/manager/download/delete.py` - Delete operations mixin
8. `backend/core/download/service.py` - Download recording service
9. `backend/alembic/versions/20251107_HHMM-{id}_add_download_model.py` - Migration
10. `frontend/src/app/media/media-details/media-downloads/media-downloads.component.ts` - Downloads display component
11. `frontend/src/app/media/media-details/media-downloads/media-downloads.component.html` - Downloads template
12. `frontend/src/app/media/media-details/media-downloads/media-downloads.component.scss` - Downloads styles

### Files to Modify:
1. `backend/core/download/video_analysis.py` - Add youtube_id, created_at, updated_at to VideoInfo
2. `backend/core/download/trailer.py` - Integrate download recording
3. `backend/api/v1/media.py` - Add downloads API endpoint
4. `frontend/src/app/models/media.ts` - Update Download interface to match new structure
5. `frontend/src/app/services/media.service.ts` - Add getDownloads method
6. `frontend/src/app/media/media-details/media-details.component.html` - Add downloads section
7. `frontend/src/app/media/media-details/media-details.component.ts` - Import MediaDownloadsComponent

---

## Backend API Implementation

### 8. Add Downloads API Endpoint (`backend/api/v1/media.py`)

Add the following imports at the top:
```python
from core.base.database.manager.download import DownloadDatabaseManager
from core.base.database.models.download import DownloadRead
```

Add this endpoint to get downloads for a specific media item (add after the existing media endpoints, around line 250):

```python
@media_router.get("/{media_id}/downloads")
async def get_media_downloads(media_id: int) -> list[DownloadRead]:
    """Get all downloads for a specific media item.
    
    Args:
        media_id (int): The ID of the media item.
        
    Returns:
        list[DownloadRead]: List of download objects for the media item.
        
    Raises:
        HTTPException: If media item not found or error retrieving downloads.
    """
    try:
        # Verify media exists first
        media_db_handler = MediaDatabaseManager()
        media = media_db_handler.read(media_id)
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Media with id {media_id} not found"
            )
        
        # Get downloads for this media using dedicated download manager
        download_db_handler = DownloadDatabaseManager()
        downloads = download_db_handler.read_all_for_media(media_id)
        return downloads
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting downloads for media {media_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving downloads: {str(e)}"
        )
```

**Note:** This uses `DownloadDatabaseManager` instead of adding methods to `MediaDatabaseManager`, keeping concerns separated.

---

## Frontend Implementation (Angular 20 with Signals)

### 9. Update Media Model (`frontend/src/app/models/media.ts`)
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Media with id {media_id} not found"
            )
        
        # Get downloads for this media
        downloads = db_handler.get_downloads_for_media(media_id)
        return downloads
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting downloads for media {media_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving downloads: {str(e)}"
        )
**Note:** This uses `DownloadDatabaseManager` instead of adding methods to `MediaDatabaseManager`, keeping concerns separated.

---

## Frontend Implementation (Angular 20 with Signals)

### 9. Update Media Model (`frontend/src/app/models/media.ts`)

Update the Download interface to match the new backend structure:

```typescript
export interface Download {
  id: number;
  path: string;
  file_name: string;
  size: number;
  resolution: string;  // e.g., "1080p", "2160p"
  file_format: string;  // e.g., "mp4", "mkv"
  video_format: string;  // e.g., "h264", "h265"
  audio_format: string;  // e.g., "aac", "ac3"
  audio_language: string | null;  // e.g., "eng", "tel"
  subtitle_format: string | null;  // e.g., "srt", "ass"
  subtitle_language: string | null;  // e.g., "eng"
  duration: number;  // in seconds
  youtube_id: string;
  file_exists: boolean;
  profile_name: string;  // Name of the TrailerProfile used
  media_id: number;
  added_at: Date;  // When trailer was downloaded
  updated_at: Date;  // When file was last modified
}

export interface Media {
  // ... existing fields ...
  downloads: Download[];  // ADD THIS if not present
}
```

### 10. Add Downloads Service Method (`frontend/src/app/services/media.service.ts`)
  audio_format: string;
  audio_channels: string;
  file_format: string;
  duration: number;
  subtitles: string;
  added_at: Date;
  profile_id: number;
  media_id: number;
  youtube_id: string;
  file_exists: boolean;
}

export interface Media {
  // ... existing fields ...
  downloads: Download[];  // ADD THIS if not present
}
```

### 11. Add Downloads Service Method (`frontend/src/app/services/media.service.ts`)

Add this method to the MediaService class:

```typescript
/**
 * Get downloads for a specific media item
 */
getDownloads(mediaId: number): Observable<Download[]> {
  return this.httpClient.get<Download[]>(`${this.mediaUrl}${mediaId}/downloads`);
}

/**
 * Scan and refresh downloads for a media item
 */
scanMediaDownloads(mediaId: number): Observable<string> {
  return this.httpClient.post<string>(`${this.mediaUrl}${mediaId}/scan`, {});
}
```

Don't forget to import Download at the top:
```typescript
import {FolderInfo, mapFolderInfo, mapMedia, Media, SearchMedia, Download} from '../models/media';
```

### 12. Create Media Downloads Component

**File: `frontend/src/app/media/media-details/media-downloads/media-downloads.component.ts`**

```typescript
import {Component, computed, effect, inject, input, resource, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MediaService} from 'src/app/services/media.service';
import {WebsocketService} from 'src/app/services/websocket.service';
import {bytesToSize, durationToTime} from 'src/app/helpers/converters';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {Download} from 'src/app/models/media';

@Component({
  selector: 'app-media-downloads',
  standalone: true,
  imports: [CommonModule, LoadIndicatorComponent],
  templateUrl: './media-downloads.component.html',
  styleUrls: ['./media-downloads.component.scss'],
})
export class MediaDownloadsComponent {
  private readonly mediaService = inject(MediaService);
  private readonly webSocketService = inject(WebsocketService);

  mediaId = input.required<number>();
  
  // Use resource signal to fetch downloads
  downloadsResource = resource<Download[], {mediaId: number}>({
    request: () => ({mediaId: this.mediaId()}),
    loader: async ({request}) => {
      return await this.mediaService.getDownloads(request.mediaId).toPromise() ?? [];
    },
  });

  isLoading = computed(() => this.downloadsResource.isLoading());
  downloads = computed(() => this.downloadsResource.value() ?? []);
  hasDownloads = computed(() => this.downloads().length > 0);

  bytesToSize = bytesToSize;
  durationToTime = durationToTime;

  refreshDownloads() {
    this.downloadsResource.reload();
  }

  getYouTubeUrl(youtubeId: string): string {
    return `https://www.youtube.com/watch?v=${youtubeId}`;
  }

  formatDate(date: Date): string {
    return new Date(date).toLocaleString();
  }
}
```

**File: `frontend/src/app/media/media-details/media-downloads/media-downloads.component.html`**

```html
<div class="downloads-section">
  <div class="downloads-header">
    <h3>Downloads</h3>
    <button class="refresh-btn" (click)="refreshDownloads()" [disabled]="isLoading()" title="Refresh Downloads">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
        <path d="M480-160q-134 0-227-93t-93-227q0-134 93-227t227-93q69 0 132 28.5T720-690v-110h80v280H520v-80h168q-32-56-87.5-88T480-720q-100 0-170 70t-70 170q0 100 70 170t170 70q77 0 139-44t87-116h84q-28 106-114 173t-196 67Z"/>
      </svg>
    </button>
  </div>

  @if (isLoading()) {
    <app-load-indicator class="center" />
  }

  @if (!isLoading() && hasDownloads()) {
    <div class="downloads-list">
      @for (download of downloads(); track download.id) {
        <div class="download-card">
          <div class="download-main">
            <div class="download-icon">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
                <path d="m320-240 160-160-160-160 56-56 216 216-216 216-56-56ZM480-80q-83 0-156-31.5T197-197q-54-54-85.5-127T80-480q0-83 31.5-156T197-763q54-54 127-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 83-31.5 156T763-197q-54 54-127 85.5T480-80Z"/>
              </svg>
            </div>
            <div class="download-info">
              <div class="download-title">{{ download.file_name }}</div>
              <div class="download-meta">
                <span class="meta-item">{{ download.resolution }}</span>
                <span class="meta-separator">•</span>
                <span class="meta-item">{{ download.video_format }}</span>
                <span class="meta-separator">•</span>
                <span class="meta-item">{{ download.audio_format }} ({{ download.audio_channels }})</span>
                <span class="meta-separator">•</span>
                <span class="meta-item">{{ bytesToSize(download.size) }}</span>
                <span class="meta-separator">•</span>
                <span class="meta-item">{{ durationToTime(download.duration) }}</span>
              </div>
              <div class="download-date">
                Added: {{ formatDate(download.added_at) }}
              </div>
            </div>
          </div>
          <div class="download-actions">
            @if (download.youtube_id) {
              <a [href]="getYouTubeUrl(download.youtube_id)" target="_blank" class="yt-link" title="View on YouTube">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                  <path d="M10,15L15.19,12L10,9V15M21.56,7.17C21.69,7.64 21.78,8.27 21.84,9.07C21.91,9.87 21.94,10.56 21.94,11.16L22,12C22,14.19 21.84,15.8 21.56,16.83C21.31,17.73 20.73,18.31 19.83,18.56C19.36,18.69 18.5,18.78 17.18,18.84C15.88,18.91 14.69,18.94 13.59,18.94L12,19C7.81,19 5.2,18.84 4.17,18.56C3.27,18.31 2.69,17.73 2.44,16.83C2.31,16.36 2.22,15.73 2.16,14.93C2.09,14.13 2.06,13.44 2.06,12.84L2,12C2,9.81 2.16,8.2 2.44,7.17C2.69,6.27 3.27,5.69 4.17,5.44C4.64,5.31 5.5,5.22 6.82,5.16C8.12,5.09 9.31,5.06 10.41,5.06L12,5C16.19,5 18.8,5.16 19.83,5.44C20.73,5.69 21.31,6.27 21.56,7.17Z" />
                </svg>
              </a>
            }
          </div>
        </div>
      }
    </div>
  }

  @if (!isLoading() && !hasDownloads()) {
    <div class="no-downloads">
      <p>No downloads recorded yet.</p>
    </div>
  }
</div>
```

**File: `frontend/src/app/media/media-details/media-downloads/media-downloads.component.scss`**

```scss
.downloads-section {
  margin: 2rem 0;
  padding: 1.5rem;
  background: var(--surface-color);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.downloads-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;

  h3 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
  }

  .refresh-btn {
    background: var(--primary-color);
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.2s, opacity 0.2s;

    &:hover:not(:disabled) {
      transform: rotate(90deg);
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    svg {
      width: 24px;
      height: 24px;
      fill: white;
    }
  }
}

.downloads-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.download-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--background-color);
  border-radius: 6px;
  border: 1px solid var(--border-color);
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
}

.download-main {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.download-icon {
  svg {
    width: 32px;
    height: 32px;
    fill: var(--primary-color);
  }
}

.download-info {
  flex: 1;

  .download-title {
    font-weight: 600;
    font-size: 1rem;
    margin-bottom: 0.25rem;
  }

  .download-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: var(--text-secondary-color);
    flex-wrap: wrap;

    .meta-separator {
      color: var(--border-color);
    }
  }

  .download-date {
    font-size: 0.75rem;
    color: var(--text-secondary-color);
    margin-top: 0.25rem;
  }
}

.download-actions {
  .yt-link {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #ff0000;
    transition: transform 0.2s;

    &:hover {
      transform: scale(1.1);
    }

    svg {
      width: 20px;
      height: 20px;
      fill: white;
    }
  }
}

.no-downloads {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary-color);
  font-style: italic;
}

@media (max-width: 768px) {
  .download-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .download-actions {
    align-self: flex-end;
    margin-top: 0.5rem;
  }
}
```

### 13. Integrate Downloads Component in Media Details

**In `frontend/src/app/media/media-details/media-details.component.ts`:**

The MediaDownloadsComponent import should already be present based on the current code. Verify it's there:

```typescript
import { MediaDownloadsComponent } from './media-downloads/media-downloads.component';

@Component({
  selector: 'app-media-details',
  imports: [
    // ... other imports ...
    MediaDownloadsComponent,  // ADD THIS if not present
  ],
  // ...
})
```

**In `frontend/src/app/media/media-details/media-details.component.html`:**

Add the downloads component BEFORE the files section. Look for the files section and add the downloads section above it:

```html
<!-- Add this section BEFORE the files component -->
@if (selectedMedia_) {
  <app-media-downloads [mediaId]="selectedMedia_.id" />
}

<!-- Existing files section below -->
<app-files [mediaId]="selectedMedia_.id" />
```

---

## Testing the Implementation

### Backend Testing:

1. **Test migration:**
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **Test API endpoint:**
   ```bash
   curl -X GET "http://localhost:7889/api/v1/media/1/downloads" \
     -H "X-API-Key: your-api-key"
   ```

### Frontend Testing:

1. **Build frontend:**
   ```bash
   cd frontend
   ng build
   ```

2. **Test in browser:**
   - Navigate to a media details page
   - The downloads section should appear before the files section
   - Downloads should load automatically using resource signals
   - Refresh button should reload downloads
   - YouTube links should open in new tab

### Integration Testing:

1. Download a trailer through the app
2. Navigate to that media's details page
3. Verify the download appears in the Downloads section
4. Verify all metadata is displayed correctly (resolution, codecs, size, duration)
5. Click the YouTube icon to verify it opens the correct video

---

# Trailer Download Tracking Implementation Task

## Objective
Implement a trailer download tracking system for the Trailarr application that records metadata about downloaded trailers in a database, allowing users to view download history and details for each media item.

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

from sqlmodel import Field

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
    updated_at: datetime
    resolution: str
    video_format: str
    audio_format: str
    audio_channels: str
    file_format: str
    duration: int = 0
    subtitles: str = "unk"
    added_at: datetime = Field(default_factory=get_current_time)
    profile_id: int
    youtube_id: str
    file_exists: bool = True


class Download(DownloadBase, table=True):
    """
    Database model for Download.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    👉Use :class:`DownloadCreate` to create/update downloads.👈 \n
    👉Use :class:`DownloadRead` to read the data.👈
    """
    
    id: int | None = Field(default=None, primary_key=True)
    media_id: int | None = Field(
        default=None, foreign_key="media.id", ondelete="CASCADE"
    )


class DownloadCreate(DownloadBase):
    """
    Model for creating/updating Download.
    """
    
    id: int | None = None
    media_id: int | None = None


class DownloadRead(DownloadBase):
    """
    Model for reading Download.
    """
    
    id: int
    media_id: int
```

**Key Points:**
- Keep it simple - no bidirectional relationships with Media model
- Only `media_id` as foreign key with CASCADE delete
- Use Python 3.13 type hints (`int | None`, not `Optional[int]`)

### 2. Create Download Service (`backend/core/download/service.py`)

Create a service to record new trailer downloads:

```python
import os
from datetime import datetime, timezone

from app_logger import ModuleLogger
from core.base.database.manager.base import MediaDatabaseManager
from core.base.database.models.download import DownloadCreate
from core.download.video_analysis import get_media_info

logger = ModuleLogger("DownloadService")


async def record_new_trailer_download(
    media_id: int,
    profile_id: int,
    file_path: str,
    youtube_video_id: str,
) -> None:
    """
    Records a new trailer download in the database.

    Args:
        media_id (int): The ID of the media.
        profile_id (int): The ID of the profile used for the download.
        file_path (str): The path to the downloaded file.
        youtube_video_id (str): The YouTube video ID of the trailer.
    """
    logger.info(f"Recording new trailer download for media {media_id}")
    try:
        # Get file stats
        file_stat = os.stat(file_path)

        # Get media info
        media_info = get_media_info(file_path)
        if not media_info:
            logger.error(f"Failed to get media info for {file_path}")
            return

        # Extract video and audio info
        video_stream = next(
            (s for s in media_info.streams if s.codec_type == "video"), None
        )
        audio_stream = next(
            (s for s in media_info.streams if s.codec_type == "audio"), None
        )
        subtitle_streams = [
            s.language for s in media_info.streams if s.codec_type == "subtitle"
        ]

        # Create download record
        download = DownloadCreate(
            path=file_path,
            file_name=os.path.basename(file_path),
            size=file_stat.st_size,
            updated_at=datetime.fromtimestamp(
                file_stat.st_mtime, tz=timezone.utc
            ),
            resolution=f"{video_stream.coded_width}x{video_stream.coded_height}"
            if video_stream
            else "N/A",
            video_format=video_stream.codec_name if video_stream else "N/A",
            audio_format=audio_stream.codec_name if audio_stream else "N/A",
            audio_channels=str(audio_stream.audio_channels)
            if audio_stream
            else "N/A",
            file_format=media_info.format_name,
            duration=media_info.duration_seconds,
            subtitles=",".join(subtitle_streams) or "unk",
            added_at=datetime.now(timezone.utc),
            profile_id=profile_id,
            media_id=media_id,
            youtube_id=youtube_video_id,
            file_exists=True,
        )

        # Save to database
        db_manager = MediaDatabaseManager()
        db_manager.create_download(download)
        logger.info(f"Successfully recorded new trailer download for media {media_id}")

    except Exception as e:
        logger.error(
            f"Failed to record new trailer download for media {media_id}: {e}"
        )
```

### 3. Update Database Manager (`backend/core/base/database/manager/base.py`)

**Add import at the top:**
```python
from core.base.database.models.download import Download, DownloadCreate
```

**Add method at the end of the `MediaDatabaseManager` class:**
```python
@manage_session
def create_download(
    self,
    download_create: DownloadCreate,
    *,
    _session: Session = None,  # type: ignore
) -> None:
    """Create a new download object in the database.\n
    Args:
        download_create (DownloadCreate): The download object to create.\n
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.\n
    Returns:
        None
    """
    db_download = Download.model_validate(download_create)
    _session.add(db_download)
    _session.commit()
    return
```

### 4. Enhance VideoInfo for YouTube ID Extraction (`backend/core/download/video_analysis.py`)

**Add `youtube_id` field to VideoInfo class:**
```python
class VideoInfo(BaseModel):
    name: str
    format_name: str
    duration_seconds: int = 0
    duration: str = "0:00:00"
    size: int = 0
    bitrate: str = "0 bps"
    streams: list[StreamInfo]
    youtube_id: str | None = None  # ADD THIS LINE
```

**Update `get_media_info` function to extract YouTube ID:**

In the `entries_required` variable, add format_tags:
```python
entries_required = (
    "format=format_name,duration,size,bit_rate :"
    " format_tags=comment,description,synopsis,YouTube,youtube_id :"  # ADD THIS
    " stream=index,codec_type,codec_name,coded_height,coded_width,channels,sample_rate"
    " : stream_tags=language,duration,name"
)
```

After parsing format info and before creating VideoInfo object, add YouTube ID extraction:
```python
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
)
```

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
    
    # ADD THIS BLOCK:
    await record_new_trailer_download(
        media_id=media.id,
        profile_id=profile.id,
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
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("resolution", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("video_format", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("audio_format", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("audio_channels", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("file_format", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("subtitles", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("youtube_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("file_exists", sa.Boolean(), nullable=False),
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

## File Summary

### New Files to Create:
1. `backend/core/base/database/models/download.py` - Download model
2. `backend/core/download/service.py` - Download recording service
3. `backend/alembic/versions/20251107_HHMM-{id}_add_download_model.py` - Migration

### Files to Modify:
1. `backend/core/base/database/manager/base.py` - Add create_download method
2. `backend/core/download/video_analysis.py` - Add YouTube ID extraction
3. `backend/core/download/trailer.py` - Integrate download recording

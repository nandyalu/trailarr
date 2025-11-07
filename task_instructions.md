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
4. `frontend/src/app/media/media-details/media-downloads/media-downloads.component.ts` - Downloads display component
5. `frontend/src/app/media/media-details/media-downloads/media-downloads.component.html` - Downloads template
6. `frontend/src/app/media/media-details/media-downloads/media-downloads.component.scss` - Downloads styles

### Files to Modify:
1. `backend/core/base/database/manager/base.py` - Add create_download method
2. `backend/core/download/video_analysis.py` - Add YouTube ID extraction
3. `backend/core/download/trailer.py` - Integrate download recording
4. `backend/api/v1/media.py` - Add downloads API endpoint
5. `frontend/src/app/models/media.ts` - Add Download interface and downloads array to Media
6. `frontend/src/app/services/media.service.ts` - Add getDownloads method
7. `frontend/src/app/media/media-details/media-details.component.html` - Add downloads section
8. `frontend/src/app/media/media-details/media-details.component.ts` - Import MediaDownloadsComponent

---

## Backend API Implementation

### 8. Add Downloads API Endpoint (`backend/api/v1/media.py`)

Add the following imports at the top:
```python
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
        db_handler = MediaDatabaseManager()
        
        # Verify media exists
        media = db_handler.read(media_id)
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
```

### 9. Add get_downloads_for_media Method to Database Manager

In `backend/core/base/database/manager/base.py`, add this method after the `create_download` method:

```python
@manage_session
def get_downloads_for_media(
    self,
    media_id: int,
    *,
    _session: Session = None,  # type: ignore
) -> list[DownloadRead]:
    """Get all downloads for a specific media item.\n
    Args:
        media_id (int): The ID of the media to get downloads for.\n
        _session (Session, Optional): A session to use for the database connection.\n
            Default is None, in which case a new session will be created.\n
    Returns:
        list[DownloadRead]: List of download objects for the media item.
    """
    from core.base.database.models.download import DownloadRead
    
    statement = select(Download).where(Download.media_id == media_id)
    downloads = _session.exec(statement).all()
    return [DownloadRead.model_validate(d) for d in downloads]
```

Also add the `select` import if not already present at the top of the file.

---

## Frontend Implementation (Angular 20 with Signals)

### 10. Update Media Model (`frontend/src/app/models/media.ts`)

The Download interface and downloads array should already be in the Media interface (they appear to exist already based on the current code). Verify this structure exists:

```typescript
export interface Download {
  id: number;
  path: string;
  file_name: string;
  size: number;
  updated_at: Date;
  resolution: string;
  video_format: string;
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

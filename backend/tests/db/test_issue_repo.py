"""Tests for db/repos/issue.py — Plan 1d coverage (entity_name join)."""

import datetime
import pytest
from sqlmodel import Session

import db.repos.issue as issue_repo
from db.engine import engine, write_session
from db.models.connection import ArrType, Connection, MonitorType
from db.models.download import Download
from db.models.issue import EntityType, Issue, IssueRead, IssueType
from db.models.media import Media
from db.models.mediatrailerstatus import MediaTrailerStatus


@write_session
def _make_connection(name: str = "Test Connection", *, _session: Session = None) -> int:  # type: ignore
    conn = Connection(
        name=name,
        arr_type=ArrType.RADARR,
        url="http://example.com",
        api_key="testkey",
        monitor=MonitorType.MONITOR_NEW,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn.id  # type: ignore


@write_session
def _make_media(connection_id: int, title: str = "Test Movie", *, _session: Session = None) -> int:  # type: ignore
    media = Media(
        connection_id=connection_id,
        arr_id=200,
        is_movie=True,
        title=title,
        clean_title=title.lower(),
        year=2024,
        language="en",
        studio="Studio",
        txdb_id="99901",
        title_slug=title.lower().replace(" ", "-"),
        monitor=True,
        arr_monitored=True,
        media_exists=False,
        media_filename="",
        season_count=0,
        runtime=100,
        added_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
    )
    _session.add(media)
    _session.commit()
    _session.refresh(media)
    return media.id  # type: ignore


@write_session
def _make_download(media_id: int, *, _session: Session = None) -> int:  # type: ignore
    download = Download(
        media_id=media_id,
        path="/media/movie/trailer.mkv",
        file_name="trailer.mkv",
        file_hash="abc123",
        size=1024,
        resolution=1080,
        file_format="mkv",
        video_format="h264",
        audio_format="aac",
        duration=120.0,
        youtube_id="test123",
        file_exists=True,
        profile_id=None,
        added_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        updated_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
    )
    _session.add(download)
    _session.commit()
    _session.refresh(download)
    return download.id  # type: ignore


@write_session
def _make_mts_row(media_id: int, *, _session: Session = None) -> int:  # type: ignore
    row = MediaTrailerStatus(
        media_id=media_id,
        profile_id=None,
        season=0,
        sequence=1,
        status="pending",
        source="app",
    )
    _session.add(row)
    _session.commit()
    _session.refresh(row)
    return row.id  # type: ignore


@write_session
def _add_issue(issue_type: IssueType, entity_type: EntityType, entity_id: int, description: str, *, _session: Session = None) -> None:  # type: ignore
    issue = Issue(
        issue_type=issue_type,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
    )
    _session.add(issue)
    _session.commit()


class TestGetAllWithEntityName:
    """1d — entity_name must be populated via SQL join."""

    def test_connection_issue_has_entity_name(self):
        conn_id = _make_connection(name="My Radarr Issue Test")
        _add_issue(IssueType.CONNECTION_FAILED, EntityType.CONNECTION, conn_id, "Test failed")

        results = issue_repo.get_all()
        conn_issues = [r for r in results if r.entity_type == EntityType.CONNECTION and r.entity_id == conn_id]
        assert conn_issues, "Expected at least one connection issue"
        assert conn_issues[0].entity_name == "My Radarr Issue Test"

    def test_download_issue_has_media_title(self):
        conn_id = _make_connection(name="DL Issue Conn")
        media_id = _make_media(conn_id, title="Inception Issue Test")
        download_id = _make_download(media_id)
        _add_issue(IssueType.FILE_DELETED, EntityType.DOWNLOAD, download_id, "File deleted")

        results = issue_repo.get_all()
        dl_issues = [r for r in results if r.entity_type == EntityType.DOWNLOAD and r.entity_id == download_id]
        assert dl_issues, "Expected at least one download issue"
        assert dl_issues[0].entity_name == "Inception Issue Test"

    def test_media_trailer_status_issue_has_media_title(self):
        conn_id = _make_connection(name="MTS Issue Conn")
        media_id = _make_media(conn_id, title="The Matrix Issue Test")
        mts_id = _make_mts_row(media_id)
        _add_issue(IssueType.FOLDER_MISSING, EntityType.MEDIA_TRAILER_STATUS, mts_id, "Folder missing")

        results = issue_repo.get_all()
        mts_issues = [r for r in results if r.entity_type == EntityType.MEDIA_TRAILER_STATUS and r.entity_id == mts_id]
        assert mts_issues, "Expected at least one media_trailer_status issue"
        assert mts_issues[0].entity_name == "The Matrix Issue Test"

    def test_nonexistent_entity_returns_null_name(self):
        _add_issue(IssueType.CONNECTION_FAILED, EntityType.CONNECTION, 999999, "Orphaned issue")

        results = issue_repo.get_all()
        orphan = [r for r in results if r.entity_type == EntityType.CONNECTION and r.entity_id == 999999]
        assert orphan, "Expected orphaned issue to be returned"
        assert orphan[0].entity_name is None

    def test_entity_type_filter_works(self):
        conn_id = _make_connection(name="Filter Test Conn")
        _add_issue(IssueType.TOKEN_INVALID, EntityType.CONNECTION, conn_id, "Token invalid")

        results = issue_repo.get_all(entity_type=EntityType.CONNECTION)
        assert all(r.entity_type == EntityType.CONNECTION for r in results)

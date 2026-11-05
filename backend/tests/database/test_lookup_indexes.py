"""The lookups per media item use an index (#732).

Without an index on `download.media_id`, `filefolderinfo.media_id` and
`filefolderinfo.parent_id`, each lookup for one media item read the whole
table. On a large library, the scan, the refresh and the download tasks
ran for hours. Old or missing statistics can make SQLite choose an index
that does not help, so `optimize_database` keeps them up to date.
"""

import sqlite3

import pytest
from sqlalchemy import create_engine, text

import database.engine as app_engine
import database.init_db  # noqa: F401 - registers every table model
from database.models.base import AppSQLModel

needs_sqlite_3_46 = pytest.mark.skipif(
    sqlite3.sqlite_version_info < (3, 46, 0),
    reason="PRAGMA optimize looks at every table from SQLite 3.46.0",
)


def _plan(connection, sql: str) -> str:
    rows = connection.execute(text(f"EXPLAIN QUERY PLAN {sql}")).fetchall()
    return " | ".join(row[3] for row in rows)


@pytest.mark.parametrize(
    "sql,index",
    [
        (
            "SELECT id FROM download WHERE media_id = 1",
            "ix_download_media_id",
        ),
        (
            "SELECT path, modified FROM filefolderinfo"
            " WHERE media_id = 1 AND type = 'FOLDER'",
            "ix_filefolderinfo_media_id",
        ),
        (
            "SELECT id FROM filefolderinfo WHERE parent_id = 1",
            "ix_filefolderinfo_parent_id",
        ),
        (
            # The check of `mark_as_restored` and `create_if_path_untracked`
            # (#733). It runs once for each restored file.
            "SELECT id FROM download"
            " WHERE path = '/m/a-trailer.mkv' AND file_exists IS 1 LIMIT 1",
            "ix_download_path",
        ),
    ],
)
def test_the_lookup_for_one_media_item_uses_an_index(tmp_path, sql, index):
    engine = create_engine(f"sqlite:///{tmp_path / 'trailarr.db'}")
    AppSQLModel.metadata.create_all(engine)
    with engine.connect() as connection:
        plan = _plan(connection, sql)
    assert index in plan
    assert "SCAN" not in plan


def _table_that_grew(engine) -> None:
    """A table analyzed with 2 rows that then grew to 5002 rows."""
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE t (id INTEGER PRIMARY KEY, media_id INT)")
        )
        connection.execute(text("CREATE INDEX ix_t_media_id ON t (media_id)"))
        connection.execute(text("INSERT INTO t (media_id) VALUES (1), (2)"))
        connection.execute(text("ANALYZE"))
        connection.execute(
            text(
                "WITH RECURSIVE n(i) AS (SELECT 1 UNION ALL"
                " SELECT i + 1 FROM n WHERE i < 5000)"
                " INSERT INTO t (media_id) SELECT i % 100 FROM n"
            )
        )


def _stat(engine) -> str:
    with engine.connect() as connection:
        return connection.execute(
            text("SELECT stat FROM sqlite_stat1 WHERE idx = 'ix_t_media_id'")
        ).scalar_one()


@needs_sqlite_3_46
def test_optimize_updates_the_statistics_of_a_table_that_grew(
    tmp_path, monkeypatch
):
    engine = create_engine(f"sqlite:///{tmp_path / 'trailarr.db'}")
    _table_that_grew(engine)
    assert _stat(engine).startswith("2 ")
    monkeypatch.setattr(app_engine, "engine", engine)

    assert app_engine.optimize_database() is True

    assert _stat(engine).startswith("5002 ")


@needs_sqlite_3_46
def test_optimize_reports_a_failure_and_does_not_raise(tmp_path, monkeypatch):
    path = tmp_path / "trailarr.db"
    _table_that_grew(create_engine(f"sqlite:///{path}"))
    read_only = create_engine(f"sqlite:///file:{path}?mode=ro&uri=true")
    monkeypatch.setattr(app_engine, "engine", read_only)

    assert app_engine.optimize_database() is False

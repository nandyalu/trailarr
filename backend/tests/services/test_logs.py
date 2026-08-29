"""Tests for services/logs.py.

The log-line parsing sat in api/v1/logs.py and had no tests. Phase 7 Stage B
moved it into a service, where it can be called with a string.
"""

from services import logs as logs_service

# A real line, as ModuleLogger writes it
REAL_LINE = (
    "2026-08-28T01:41:48-0500 [INFO|main|L075]: Main: Starting Trailarr application"
)


class TestParseLogLine:

    def test_a_normal_line_is_split_into_fields(self):
        record = logs_service.parse_log_line(REAL_LINE)
        assert record["datetime"] == "2026-08-28T01:41:48-0500"
        assert record["level"] == "INFO"
        assert record["filename"] == "main"
        assert record["lineno"] == 75
        assert record["module"] == "Main"
        assert record["message"] == "Starting Trailarr application"
        assert record["raw_log"] == REAL_LINE

    def test_the_module_prefix_is_taken_out_of_the_message(self):
        line = "2026-08-28T01:41:48-0500 [WARNING|binaries|L041]: BinaryPaths: no ffmpeg"
        record = logs_service.parse_log_line(line)
        assert record["module"] == "BinaryPaths"
        assert record["message"] == "no ffmpeg"

    def test_a_job_line_is_filed_under_tasks(self):
        line = "2026-08-28T01:41:48-0500 [INFO|scheduler|L456]: Job 38f0 completed"
        record = logs_service.parse_log_line(line)
        assert record["module"] == "Tasks"

    def test_a_line_that_does_not_match_is_kept_whole(self):
        """Nothing is dropped: the line becomes the message."""
        line = "a traceback line with no prefix at all"
        record = logs_service.parse_log_line(line)
        assert record["level"] == "INFO"
        assert record["module"] == "Other"
        assert record["message"] == line
        assert record["raw_log"] == line

    def test_an_empty_line_still_gives_a_record(self):
        record = logs_service.parse_log_line("")
        assert record["message"] == ""
        assert record["module"] == "Other"

    def test_the_line_number_is_an_int(self):
        record = logs_service.parse_log_line(REAL_LINE)
        assert isinstance(record["lineno"], int)

    def test_every_record_has_the_fields_the_log_model_needs(self):
        """The handler builds Log(**record), so the keys must all be there."""
        expected = {
            "datetime",
            "level",
            "filename",
            "lineno",
            "module",
            "message",
            "raw_log",
        }
        assert set(logs_service.parse_log_line(REAL_LINE)) == expected
        assert set(logs_service.parse_log_line("junk")) == expected
        assert set(logs_service.no_logs_record()) == expected


class TestDownloadHelpers:

    def test_the_download_name_is_stamped_and_ends_with_log(self):
        name = logs_service.download_file_name()
        assert name.startswith("trailarr_logs_")
        assert name.endswith(".log")

    def test_no_file_means_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            logs_service, "logs_dir", lambda: str(tmp_path / "nothing-here")
        )
        assert logs_service.log_file_to_download() is None

    def test_an_existing_file_is_returned(self, tmp_path, monkeypatch):
        (tmp_path / "trailarr.log").write_text("hello")
        monkeypatch.setattr(logs_service, "logs_dir", lambda: str(tmp_path))
        assert logs_service.log_file_to_download() == f"{tmp_path}/trailarr.log"

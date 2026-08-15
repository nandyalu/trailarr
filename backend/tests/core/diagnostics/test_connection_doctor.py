"""Tests for the Connection Doctor (Onboarding track, Milestone A).

Probes run against real temporary directories; the Arr/Plex API and the
DB media samples are patched. Wargame scenarios A1–A6 from
plans/track-onboarding-diagnostics.md each have a test here.
"""

import os
import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from sqlmodel import Session

from core.base.database.models.connection import ArrType, Connection
from core.base.database.utils.engine import write_session
from core.diagnostics import connection_doctor
from core.diagnostics.models import ProbeStatus

PKG = "core.diagnostics.connection_doctor"


@write_session
def _make_conn(
    name: str, *, _session: Session = None  # type: ignore
) -> int:
    conn = Connection(
        name=name,
        arr_type=ArrType.RADARR,
        url="http://localhost:7878",
        api_key="key",
        monitor_new_media=True,
    )
    _session.add(conn)
    _session.commit()
    _session.refresh(conn)
    return conn.id  # type: ignore


def _patched(roots, samples=None, bases=None, search_roots=None):
    """Patch API roots, media samples, suggester bases, and search roots.

    search_roots defaults to [] so tests never walk the real disk; pass
    a tmp-path root to exercise the by-name search stage.
    """
    return (
        patch(
            f"{PKG}.connection_manager.get_rootfolders",
            return_value=roots,
        ),
        patch(
            f"{PKG}._arr_side_media_samples",
            return_value=samples or [],
        ),
        patch(f"{PKG}._visible_bases", return_value=bases or []),
        patch(f"{PKG}._search_roots", return_value=search_roots or []),
    )


def _probe(report, kind, name_part=""):
    for p in report.probes:
        if p.kind == kind and name_part in p.name:
            return p
    raise AssertionError(f"no {kind} probe matching '{name_part}'")


class TestPathVisibility:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.conn_id = _make_conn(f"Doc-{uuid.uuid4().hex[:8]}")
        self.tmp = tmp_path

    @pytest.mark.asyncio
    async def test_visible_root_is_healthy(self):
        movies = self.tmp / "movies"
        (movies / "Film A").mkdir(parents=True)
        p1, p2, p3, p4 = _patched([str(movies)])
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        assert report.status == "healthy"
        probe = _probe(report, "path_visibility")
        assert probe.status == ProbeStatus.OK
        assert "1 entries" in probe.detail

    @pytest.mark.asyncio
    async def test_invisible_root_is_an_error(self):
        p1, p2, p3, p4 = _patched(["/nonexistent/remote/movies"])
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        assert report.status == "issues"
        probe = _probe(report, "path_visibility")
        assert probe.status == ProbeStatus.ERROR
        assert "not visible" in probe.detail

    @pytest.mark.asyncio
    async def test_empty_root_is_a_warning_not_a_pass(self):
        """A2: silently-empty mounts must not report healthy."""
        empty = self.tmp / "mount"
        empty.mkdir()
        p1, p2, p3, p4 = _patched([str(empty)])
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        assert report.status == "issues"
        probe = _probe(report, "path_visibility")
        assert probe.status == ProbeStatus.WARNING
        assert "reachable but empty" in probe.detail
        assert probe.docs_url.endswith("network-drives/")

    @pytest.mark.asyncio
    async def test_bare_metal_identity_short_circuits(self):
        """A4: when the path exists as reported, no mapping is suggested."""
        movies = self.tmp / "movies"
        (movies / "Film A").mkdir(parents=True)
        p1, p2, p3, p4 = _patched([str(movies)], bases=["/somewhere"])
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        probe = _probe(report, "path_visibility")
        assert probe.status == ProbeStatus.OK
        assert probe.suggested_mapping is None

    @pytest.mark.asyncio
    async def test_windows_path_on_posix_is_explained(self):
        """A5: Windows-style Arr paths get a targeted explanation."""
        if os.name == "nt":
            pytest.skip("POSIX-host scenario")
        p1, p2, p3, p4 = _patched(["C:\\Media\\Movies"])
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        probe = _probe(report, "path_style")
        assert probe.status == ProbeStatus.ERROR
        assert "Windows path" in probe.detail
        assert "path mapping" in probe.remediation


class TestMappingSuggester:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.conn_id = _make_conn(f"Sug-{uuid.uuid4().hex[:8]}")
        self.tmp = tmp_path
        # Visible library: /<tmp>/media/{movies,tv}/<items>
        self.local = tmp_path / "media"
        (self.local / "movies" / "Film A").mkdir(parents=True)
        (self.local / "movies" / "Film B").mkdir(parents=True)
        (self.local / "tv" / "Show A").mkdir(parents=True)

    @pytest.mark.asyncio
    async def test_suggests_mapping_with_corroborating_samples(self):
        """The Arr path /data/movies is invisible, but its tail exists
        under a visible base and the media samples confirm it."""
        p1, p2, p3, p4 = _patched(
            ["/data/movies"],
            samples=["/data/movies/Film A", "/data/movies/Film B"],
            bases=[str(self.local)],
        )
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        probe = _probe(report, "path_visibility")
        assert probe.suggested_mapping is not None
        assert probe.suggested_mapping.path_from == "/data/"
        assert probe.suggested_mapping.path_to == str(self.local) + "/"
        assert probe.suggested_mapping.corroborations == 3
        assert "Suggested mapping" in probe.remediation

    @pytest.mark.asyncio
    async def test_multiple_roots_get_per_root_suggestions(self):
        """A1: each root is probed and suggested on its own."""
        p1, p2, p3, p4 = _patched(
            ["/data/movies", "/data/tv"],
            samples=["/data/movies/Film A", "/data/tv/Show A"],
            bases=[str(self.local)],
        )
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        probes = [
            p for p in report.probes if p.kind == "path_visibility"
        ]
        assert len(probes) == 2
        for probe in probes:
            assert probe.suggested_mapping is not None
            assert probe.suggested_mapping.path_from == "/data/"

    @pytest.mark.asyncio
    async def test_single_sample_suggestion_is_marked_low_confidence(self):
        """A1: a name-only match must say so instead of claiming certainty."""
        p1, p2, p3, p4 = _patched(
            ["/data/movies"], samples=[], bases=[str(self.local)]
        )
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        probe = _probe(report, "path_visibility")
        assert probe.suggested_mapping is not None
        assert probe.suggested_mapping.corroborations == 1
        assert "folder name only" in probe.remediation

    @pytest.mark.asyncio
    async def test_single_component_root_matches_by_name(self):
        """Radarr reports '/movies'; the visible '/…/media/movies' folder
        carries the same name, so the direct mapping is suggested."""
        p1, p2, p3, p4 = _patched(
            ["/movies"],
            samples=[],
            bases=[str(self.local), str(self.local / "movies")],
        )
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        probe = _probe(report, "path_visibility")
        assert probe.suggested_mapping is not None
        assert probe.suggested_mapping.path_from == "/movies/"
        assert probe.suggested_mapping.path_to == str(self.local / "movies") + "/"

    @pytest.mark.asyncio
    async def test_no_suggestion_when_nothing_matches(self):
        p1, p2, p3, p4 = _patched(
            ["/data/anime"], samples=[], bases=[str(self.local)]
        )
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        probe = _probe(report, "path_visibility")
        assert probe.suggested_mapping is None
        assert probe.status == ProbeStatus.ERROR


class TestSearchBasedSuggestions:
    """The by-name media folder search (stage 1 of the suggester).

    Reproduces the two real-library failures the shallow heuristic had:
    a library nested too deep for the base walk (no suggestion at all),
    and a folder-name coincidence that produced a wrong suggestion.
    """

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.conn_id = _make_conn(f"Search-{uuid.uuid4().hex[:8]}")
        self.tmp = tmp_path
        # Real library, three levels deep: <tmp>/media/all/Media/...
        self.deep = tmp_path / "media" / "all" / "Media"
        (self.deep / "tv" / "Show A (2020) {tvdb-1}").mkdir(parents=True)
        (self.deep / "tv" / "Show B (2021) {tvdb-2}").mkdir(parents=True)
        (self.deep / "movies" / "all" / "Film X {imdb-tt1}").mkdir(
            parents=True
        )
        self.search_roots = [str(tmp_path / "media")]

    @pytest.mark.asyncio
    async def test_deep_library_found_by_media_folder_name(self):
        """Sonarr case: '/media/tv' invisible, files at
        <tmp>/media/all/Media/tv — too deep for the base walk, found by
        searching for the tracked series folder's name."""
        p1, p2, p3, p4 = _patched(
            ["/media/tv"],
            samples=[
                "/media/tv/Show A (2020) {tvdb-1}",
                "/media/tv/Show B (2021) {tvdb-2}",
            ],
            bases=[],
            search_roots=self.search_roots,
        )
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        probe = _probe(report, "path_visibility")
        assert probe.suggested_mapping is not None
        assert probe.suggested_mapping.path_from == "/media/"
        assert probe.suggested_mapping.path_to == str(
            self.tmp / "media" / "all" / "Media"
        ) + "/"
        # found folder + resolving root + the other series folder
        assert probe.suggested_mapping.corroborations == 3
        assert "confirm it" in probe.remediation

    @pytest.mark.asyncio
    async def test_search_beats_folder_name_coincidence(self):
        """Radarr case: a visible dir named 'all' tail-matches
        '/media/movies/all' and used to produce a wrong suggestion.
        The by-name search finds the real location and wins."""
        decoy_base = str(self.tmp / "media")  # contains a dir named 'all'
        p1, p2, p3, p4 = _patched(
            ["/media/movies/all"],
            samples=["/media/movies/all/Film X {imdb-tt1}"],
            bases=[decoy_base],
            search_roots=self.search_roots,
        )
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        probe = _probe(report, "path_visibility")
        assert probe.suggested_mapping is not None
        # NOT the decoy ('/media/movies/' -> <tmp>/media/)
        assert probe.suggested_mapping.path_from == "/media/"
        assert probe.suggested_mapping.path_to == str(
            self.tmp / "media" / "all" / "Media"
        ) + "/"
        assert probe.suggested_mapping.corroborations == 2

    @pytest.mark.asyncio
    async def test_sibling_roots_reuse_the_found_mapping(self):
        """The search runs once; sibling roots reuse the derived mapping."""
        p1, p2, p3, p4 = _patched(
            ["/media/tv", "/media/movies/all"],
            samples=[
                "/media/tv/Show A (2020) {tvdb-1}",
                "/media/movies/all/Film X {imdb-tt1}",
            ],
            bases=[],
            search_roots=self.search_roots,
        )
        with (
            p1, p2, p3, p4,
            patch(
                f"{PKG}._suggest_from_search",
                wraps=connection_doctor._suggest_from_search,
            ) as spy,
        ):
            report = await connection_doctor.run_doctor(self.conn_id)
        probes = [p for p in report.probes if p.kind == "path_visibility"]
        assert len(probes) == 2
        for probe in probes:
            assert probe.suggested_mapping is not None
            assert probe.suggested_mapping.path_from == "/media/"
        # Second root resolved from the known mapping without a new search
        assert spy.call_count == 1

    @pytest.mark.asyncio
    async def test_falls_back_to_tail_match_when_search_finds_nothing(self):
        """Search finding nothing keeps the old heuristic working."""
        local = self.tmp / "flat"
        (local / "movies").mkdir(parents=True)
        p1, p2, p3, p4 = _patched(
            ["/data/movies"],
            samples=["/data/movies/Unknown Film (1999)"],
            bases=[str(local)],
            search_roots=[str(local)],  # 'Unknown Film' is not on disk
        )
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        probe = _probe(report, "path_visibility")
        assert probe.suggested_mapping is not None
        assert probe.suggested_mapping.path_from == "/data/"
        assert probe.suggested_mapping.path_to == str(local) + "/"


class TestSearchHelpers:

    def test_align_suffix_deep_library(self):
        assert connection_doctor._align_suffix(
            "/media/tv/Show X", "/media/all/Media/tv/Show X"
        ) == ("/media/", "/media/all/Media/")

    def test_align_suffix_stops_at_case_difference(self):
        # 'media' != 'Media' — the suffix stops before it
        assert connection_doctor._align_suffix(
            "/media/movies/all/Film X",
            "/srv/x/Media/movies/all/Film X",
        ) == ("/media/", "/srv/x/Media/")

    def test_align_suffix_windows_remote(self):
        assert connection_doctor._align_suffix(
            "C:\\Media\\Movies\\Film X", "/media/movies/Film X"
        ) == ("C:\\Media\\Movies\\", "/media/movies/")

    def test_align_suffix_keeps_one_remote_component(self):
        # The whole remote path may match — the mapping must never
        # claim the filesystem root
        result = connection_doctor._align_suffix(
            "/tv/Show X", "/media/tv/Show X"
        )
        assert result == ("/tv/", "/media/tv/")

    def test_align_suffix_identity_returns_none(self):
        assert connection_doctor._align_suffix(
            "/media/tv/Show X", "/media/tv/Show X"
        ) is None

    def test_search_finds_deep_folder(self, tmp_path):
        target = tmp_path / "a" / "b" / "c" / "Needle (2020)"
        target.mkdir(parents=True)
        hits = connection_doctor._search_media_folder(
            "Needle (2020)", [str(tmp_path)]
        )
        assert hits == [str(target)]

    def test_search_respects_depth_cap(self, tmp_path):
        deep = tmp_path / "a" / "b" / "c" / "d" / "e" / "Needle (2020)"
        deep.mkdir(parents=True)
        hits = connection_doctor._search_media_folder(
            "Needle (2020)", [str(tmp_path)], max_depth=2
        )
        assert hits == []

    def test_search_respects_entry_budget(self, tmp_path):
        for i in range(20):
            (tmp_path / f"dir{i:02}").mkdir()
        (tmp_path / "zz" ).mkdir()
        (tmp_path / "zz" / "Needle (2020)").mkdir()
        hits = connection_doctor._search_media_folder(
            "Needle (2020)", [str(tmp_path)], budget=5
        )
        assert hits == []


class TestPermissions:

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.conn_id = _make_conn(f"Perm-{uuid.uuid4().hex[:8]}")
        self.tmp = tmp_path

    @pytest.mark.asyncio
    async def test_writable_folder_passes_and_leaves_no_files(self):
        """A6: the write test cleans up after itself."""
        movies = self.tmp / "movies"
        (movies / "Film A").mkdir(parents=True)
        p1, p2, p3, p4 = _patched([str(movies)])
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        probe = _probe(report, "permissions")
        assert probe.status == ProbeStatus.OK
        assert not (movies / ".trailarr-write-test").exists()

    @pytest.mark.asyncio
    async def test_readonly_folder_names_uid_gid_fix(self):
        if os.name == "nt" or os.getuid() == 0:
            pytest.skip("chmod-based denial needs a non-root POSIX user")
        movies = self.tmp / "movies"
        (movies / "Film A").mkdir(parents=True)
        movies.chmod(0o555)
        try:
            p1, p2, p3, p4 = _patched([str(movies)])
            with p1, p2, p3, p4:
                report = await connection_doctor.run_doctor(self.conn_id)
        finally:
            movies.chmod(0o755)
        probe = _probe(report, "permissions")
        assert probe.status == ProbeStatus.ERROR
        assert "uid=" in probe.detail
        assert "PUID/PGID" in probe.remediation
        assert probe.docs_url.endswith("environment-variables/")

    @pytest.mark.asyncio
    async def test_no_accessible_folder_skips_write_test(self):
        p1, p2, p3, p4 = _patched(["/nonexistent/remote"])
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        probe = _probe(report, "permissions")
        assert probe.status == ProbeStatus.SKIPPED


class TestReachabilityAndReports:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.conn_id = _make_conn(f"Reach-{uuid.uuid4().hex[:8]}")

    @pytest.mark.asyncio
    async def test_unreachable_api_is_reported_not_raised(self):
        with (
            patch(
                f"{PKG}.connection_manager.get_rootfolders",
                side_effect=ConnectionError("connection refused"),
            ),
            patch(f"{PKG}._arr_side_media_samples", return_value=[]),
            patch(f"{PKG}._visible_bases", return_value=[]),
        ):
            report = await connection_doctor.run_doctor(self.conn_id)
        assert report.status == "issues"
        probe = _probe(report, "reachability")
        assert probe.status == ProbeStatus.ERROR
        assert "connection refused" in probe.detail

    @pytest.mark.asyncio
    async def test_report_is_stored_and_forgotten(self):
        p1, p2, p3, p4 = _patched([])
        with p1, p2, p3, p4:
            await connection_doctor.run_doctor(self.conn_id)
        assert connection_doctor.get_report(self.conn_id) is not None
        assert any(
            r.connection_id == self.conn_id
            for r in connection_doctor.get_all_reports()
        )
        connection_doctor.forget_report(self.conn_id)
        assert connection_doctor.get_report(self.conn_id) is None

    @pytest.mark.asyncio
    async def test_no_roots_reported_is_a_skip_not_a_pass(self):
        p1, p2, p3, p4 = _patched([])
        with p1, p2, p3, p4:
            report = await connection_doctor.run_doctor(self.conn_id)
        probe = _probe(report, "path_visibility")
        assert probe.status == ProbeStatus.SKIPPED
        assert "no root folders" in probe.detail


class TestVisibleBases:

    def test_system_dirs_are_excluded(self, tmp_path):
        conn = SimpleNamespace(path_mappings=[])
        bases = connection_doctor._visible_bases(conn)
        assert "/proc" not in bases
        assert "/sys" not in bases
        assert "/etc" not in bases

    def test_existing_mapping_targets_are_included(self):
        conn = SimpleNamespace(
            path_mappings=[
                SimpleNamespace(
                    path_from="/x/", path_to="/nonexistent-target/"
                )
            ]
        )
        bases = connection_doctor._visible_bases(conn)
        assert "/nonexistent-target" in bases

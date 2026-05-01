import pytest
from core.plex.connection_manager import _resolve_show_root


class TestResolveShowRoot:
    """Tests for _resolve_show_root — signal 1 (regex) and signal 2 (fuzzy)."""

    # --- Signal 1: season folder regex ---

    def test_season_folder_stripped(self):
        assert _resolve_show_root("/tv/Show/Season 1", "Show") == "/tv/Show"

    def test_season_s_format(self):
        assert _resolve_show_root("/tv/Show/S02", "Show") == "/tv/Show"

    def test_season_series_format(self):
        assert _resolve_show_root("/tv/Show/Series 3", "Show") == "/tv/Show"

    def test_localized_saison(self):
        assert _resolve_show_root("/tv/Show/Saison 3", "Show") == "/tv/Show"

    def test_localized_staffel(self):
        assert _resolve_show_root("/tv/Show/Staffel 2", "Show") == "/tv/Show"

    def test_localized_temporada(self):
        assert _resolve_show_root("/tv/Show/Temporada 1", "Show") == "/tv/Show"

    def test_specials_folder(self):
        assert _resolve_show_root("/tv/Show/Specials", "Show") == "/tv/Show"

    def test_extras_folder(self):
        assert _resolve_show_root("/tv/Show/Extras", "Show") == "/tv/Show"

    def test_bonus_folder(self):
        assert _resolve_show_root("/tv/Show/Bonus", "Show") == "/tv/Show"

    # --- Signal 2: fuzzy title match (already at show root) ---

    def test_already_at_root_plain(self):
        result = _resolve_show_root("/tv/Breaking Bad", "Breaking Bad")
        assert result == "/tv/Breaking Bad"

    def test_already_at_root_with_year(self):
        result = _resolve_show_root("/tv/Breaking Bad (2008)", "Breaking Bad")
        assert result == "/tv/Breaking Bad (2008)"

    def test_already_at_root_with_tvdb_id(self):
        result = _resolve_show_root(
            "/tv/The Boys (2019) {tvdb-355567}", "The Boys"
        )
        assert result == "/tv/The Boys (2019) {tvdb-355567}"

    def test_already_at_root_with_multiple_ids(self):
        result = _resolve_show_root(
            "/tv/Lost (2004) {tvdb-73739} [imdb-tt0411008]", "Lost"
        )
        assert result == "/tv/Lost (2004) {tvdb-73739} [imdb-tt0411008]"

    def test_short_title_heavy_decoration(self):
        # Short title must still match after decorator stripping
        result = _resolve_show_root(
            "/tv/Lost (2004) {tvdb-73739}", "Lost"
        )
        assert result == "/tv/Lost (2004) {tvdb-73739}"

    def test_title_with_country_disambiguator(self):
        # "(US)" is not a year so it stays after stripping; ratio still high
        result = _resolve_show_root(
            "/tv/The Office (US) (2005)", "The Office"
        )
        assert result == "/tv/The Office (US) (2005)"

    # --- Ambiguous: neither signal fires → return unchanged ---

    def test_ambiguous_disc_folder_stays(self):
        # "Disc 1" matches neither season regex nor the show title
        result = _resolve_show_root("/tv/Show/Disc 1", "Show")
        assert result == "/tv/Show/Disc 1"

    # --- Edge cases ---

    def test_empty_folder_returns_empty(self):
        assert _resolve_show_root("", "Show") == ""

    def test_empty_title_falls_through(self):
        # Empty title disables fuzzy check; regex still works
        assert _resolve_show_root("/tv/Show/Season 1", "") == "/tv/Show"

    def test_root_path_unchanged(self):
        assert _resolve_show_root("/", "Show") == "/"

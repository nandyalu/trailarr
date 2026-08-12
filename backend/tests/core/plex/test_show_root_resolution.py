from core.plex.connection_manager import _resolve_show_root


class TestResolveShowRoot:
    """Tests for _resolve_show_root — season-folder stripping."""

    # --- Season folder regex: strip one level ---

    def test_season_folder_stripped(self):
        assert _resolve_show_root("/tv/Show/Season 1") == "/tv/Show"

    def test_season_s_format(self):
        assert _resolve_show_root("/tv/Show/S02") == "/tv/Show"

    def test_season_series_format(self):
        assert _resolve_show_root("/tv/Show/Series 3") == "/tv/Show"

    def test_localized_saison(self):
        assert _resolve_show_root("/tv/Show/Saison 3") == "/tv/Show"

    def test_localized_staffel(self):
        assert _resolve_show_root("/tv/Show/Staffel 2") == "/tv/Show"

    def test_localized_temporada(self):
        assert _resolve_show_root("/tv/Show/Temporada 1") == "/tv/Show"

    def test_specials_folder(self):
        assert _resolve_show_root("/tv/Show/Specials") == "/tv/Show"

    def test_extras_folder(self):
        assert _resolve_show_root("/tv/Show/Extras") == "/tv/Show"

    def test_bonus_folder(self):
        assert _resolve_show_root("/tv/Show/Bonus") == "/tv/Show"

    # --- Already at show root: return unchanged ---

    def test_already_at_root_plain(self):
        assert _resolve_show_root("/tv/Breaking Bad") == "/tv/Breaking Bad"

    def test_already_at_root_with_year(self):
        result = _resolve_show_root("/tv/Breaking Bad (2008)")
        assert result == "/tv/Breaking Bad (2008)"

    def test_already_at_root_with_tvdb_id(self):
        result = _resolve_show_root("/tv/The Boys (2019) {tvdb-355567}")
        assert result == "/tv/The Boys (2019) {tvdb-355567}"

    def test_already_at_root_with_multiple_ids(self):
        result = _resolve_show_root(
            "/tv/Lost (2004) {tvdb-73739} [imdb-tt0411008]"
        )
        assert result == "/tv/Lost (2004) {tvdb-73739} [imdb-tt0411008]"

    # --- Unrecognized last component: return unchanged ---

    def test_ambiguous_disc_folder_stays(self):
        # "Disc 1" does not match the season regex — folder is kept as-is;
        # the prefix match in read_by_folder_path is the safety net.
        assert _resolve_show_root("/tv/Show/Disc 1") == "/tv/Show/Disc 1"

    # --- Edge cases ---

    def test_empty_folder_returns_empty(self):
        assert _resolve_show_root("") == ""

    def test_root_path_unchanged(self):
        assert _resolve_show_root("/") == "/"

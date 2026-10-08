"""Type-aware satisfaction — plans/phase-09-video-types.md decision 3,
wargames W1 and W4.

A profile owns its downloads by id, whatever their type. A claim is
different: an unattributed file can only satisfy a profile of its own
type. A featurette on disk never counts as the trailer.
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from unittest.mock import patch

from database.models.mediavideo import VideoSource
from services.satisfaction import evaluate_satisfaction

NOW = datetime(2026, 10, 7, tzinfo=timezone.utc)


def _download(
    download_id: int,
    profile_id: int = 0,
    video_type: str = "trailer",
    age_hours: int = 0,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=download_id,
        profile_id=profile_id,
        file_exists=True,
        video_type=video_type,
        youtube_id="unknown0000",
        added_at=NOW - timedelta(hours=age_hours),
    )


def _profile(
    profile_id: int, video_type: str = "trailer", priority: int = 100
) -> SimpleNamespace:
    return SimpleNamespace(
        id=profile_id,
        priority=priority,
        upgrade_to_tmdb=False,
        video_type=video_type,
    )


def _media(downloads: list) -> SimpleNamespace:
    return SimpleNamespace(id=1, title="Test", downloads=downloads)


class TestClaimsMatchOnType:
    def test_a_featurette_file_does_not_satisfy_a_trailer_profile(self):
        trailer = _profile(1)
        media = _media([_download(10, video_type="featurette")])

        result = evaluate_satisfaction(media, [trailer])

        assert result.claims == []
        assert [p.id for p in result.unsatisfied] == [1]

    def test_a_featurette_file_satisfies_a_featurette_profile(self):
        featurette = _profile(2, "featurette")
        media = _media([_download(10, video_type="featurette")])

        result = evaluate_satisfaction(media, [featurette])

        assert result.claims == [(10, 2)]
        assert result.unsatisfied == []
        assert result.details[0].via == "claim"

    def test_each_profile_claims_the_file_of_its_type(self):
        trailer, featurette = _profile(1), _profile(2, "featurette")
        media = _media(
            [
                _download(10, video_type="featurette", age_hours=5),
                _download(11, video_type="trailer", age_hours=1),
            ]
        )

        result = evaluate_satisfaction(media, [trailer, featurette])

        assert sorted(result.claims) == [(10, 2), (11, 1)]
        assert result.unsatisfied == []

    def test_the_oldest_file_of_the_type_is_claimed_first(self):
        trailer = _profile(1)
        media = _media(
            [
                _download(10, video_type="featurette", age_hours=9),
                _download(11, video_type="trailer", age_hours=2),
                _download(12, video_type="trailer", age_hours=7),
            ]
        )

        result = evaluate_satisfaction(media, [trailer])

        assert result.claims == [(12, 1)]


class TestOwnershipIgnoresType:
    """W1: a download that a profile owns keeps the profile satisfied
    whatever its label says. The profile's type change relabels its
    downloads, so the two agree after a change; and until they do, the
    profile must not download again."""

    def test_an_owned_download_of_another_label_still_satisfies(self):
        profile = _profile(1, "featurette")
        media = _media([_download(10, profile_id=1, video_type="trailer")])

        result = evaluate_satisfaction(media, [profile])

        assert result.unsatisfied == []
        assert result.details[0].via == "own_download"


class TestPendingProfileWithUnclaimableFile:
    """W4: a pending trailer profile coexists with an unattributed
    featurette. The trailer profile stays pending (it downloads), and the
    featurette stays unattributed."""

    def test_the_trailer_profile_is_pending_and_the_file_stays(self):
        trailer = _profile(1)
        media = _media([_download(10, video_type="featurette")])

        result = evaluate_satisfaction(media, [trailer])

        assert [p.id for p in result.unsatisfied] == [1]
        assert result.claims == []


def _candidate(video_id: str, video_type: str, source=VideoSource.TMDB):
    return SimpleNamespace(
        video_id=video_id, source=source, language="en", video_type=video_type
    )


class TestUpgradePerType:
    """Copilot review on #701: the upgrade must read the candidates of the
    profile's own type. A featurette profile that owns a TMDB featurette
    is satisfied, even when the list holds trailers too; and it never
    replaces its featurette with a trailer."""

    def _featurette_profile(self):
        profile = _profile(2, "featurette")
        profile.upgrade_to_tmdb = True
        profile.always_search = False
        profile.language = ""
        profile.replace_unknown_videos = False
        return profile

    def test_an_owned_tmdb_featurette_keeps_the_profile_satisfied(self):
        profile = self._featurette_profile()
        download = _download(10, profile_id=2, video_type="featurette")
        download.youtube_id = "feat1"
        media = _media([download])
        videos = [
            _candidate("trail1", "trailer"),
            _candidate("feat1", "featurette"),
            _candidate("feat2", "featurette"),
        ]
        with patch(
            "services.trailers.resolver.app_settings"
        ) as settings:
            settings.tmdb_api_key = "key"
            result = evaluate_satisfaction(media, [profile], videos)
        assert result.unsatisfied == []
        assert result.details[0].upgrade_state == "matched"

    def test_a_profile_without_a_video_of_its_type_waits_for_tmdb(self):
        profile = self._featurette_profile()
        download = _download(10, profile_id=2, video_type="featurette")
        download.youtube_id = "old1"
        media = _media([download])
        videos = [_candidate("trail1", "trailer")]
        with patch(
            "services.trailers.resolver.app_settings"
        ) as settings:
            settings.tmdb_api_key = "key"
            result = evaluate_satisfaction(media, [profile], videos)
        assert result.unsatisfied == []
        assert result.details[0].upgrade_state == "awaiting_tmdb"

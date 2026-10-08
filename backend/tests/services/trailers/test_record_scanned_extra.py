"""A download row for an extra that a person placed is recorded without
a hash — code review of Phase 9, finding 13.

The hash exists so that the scan recognizes a trailer that Trailarr made
after a rename. A 20 GB featurette would be read in full for a hash that
nothing uses. The ffprobe stays: the row needs the duration and the
streams.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from services.trailers.trailers import service
from services.trailers.video_analysis import StreamInfo, VideoInfo

NOW = datetime(2026, 10, 8, tzinfo=timezone.utc)


def _info(path: str) -> VideoInfo:
    return VideoInfo(
        name="x",
        file_path=path,
        format_name="matroska",
        duration_seconds=90,
        size=10,
        streams=[
            StreamInfo(index=0, codec_type="video", codec_name="h264", coded_height=1080),
            StreamInfo(index=1, codec_type="audio", codec_name="aac"),
        ],
        created_at=NOW,
        updated_at=NOW,
    )


def _media():
    return SimpleNamespace(id=1, title="Hashed Movie")


class TestTheHashIsForTrailersOnly:
    async def _record(self, path: str, video_type: str):
        with (
            patch.object(service, "get_media_info", return_value=_info(path)),
            patch.object(service.os, "stat") as stat,
            patch.object(
                service, "compute_file_hash", return_value="sha"
            ) as hashed,
            patch.object(service.download_manager, "create") as create,
        ):
            stat.return_value = SimpleNamespace(st_mtime=0.0, st_ctime=0.0)
            ok = await service.record_new_trailer_download(
                _media(), 0, path, video_type=video_type
            )
        assert ok is True
        [row] = create.call_args.args
        return hashed, row

    @pytest.mark.asyncio
    async def test_a_featurette_is_probed_but_not_hashed(self):
        hashed, row = await self._record("/m/Featurettes/Making Of.mkv", "featurette")
        hashed.assert_not_called()
        assert row.file_hash == ""
        assert row.video_type == "featurette"
        assert row.duration == 90

    @pytest.mark.asyncio
    async def test_a_trailer_is_hashed(self):
        hashed, row = await self._record("/m/Movie-trailer.mkv", "trailer")
        hashed.assert_called_once_with("/m/Movie-trailer.mkv")
        assert row.file_hash == "sha"

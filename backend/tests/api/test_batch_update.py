"""Tests for the delete action of batch_update_media in api/v1/media.py."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from api.v1.media import batch_update_media
from api.v1.models import BatchUpdate


def ok_result(media_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        ok=True, message=f"Deleted the trailers of {media_id}.", reload="media"
    )


class TestBatchDelete:

    @pytest.mark.asyncio
    async def test_a_failed_item_sends_one_message_and_the_batch_goes_on(
        self,
    ):
        """H15: a failed item used to send two messages ("Error deleting
        trailer!" and then "Error updating Media!"), and the batch stopped at
        that item."""

        async def delete_trailers(media_id: int):
            if media_id == 2:
                raise RuntimeError("disk is gone")
            return ok_result(media_id)

        with (
            patch(
                "api.v1.media.media_service.delete_trailers",
                new=AsyncMock(side_effect=delete_trailers),
            ) as mock_delete,
            patch(
                "api.v1.media.websockets.ws_manager.broadcast",
                new=AsyncMock(),
            ) as mock_broadcast,
        ):
            await batch_update_media(
                BatchUpdate(media_ids=[1, 2, 3], action="delete")
            )

        assert [c.args[0] for c in mock_delete.await_args_list] == [1, 2, 3]
        messages = [c.args[0] for c in mock_broadcast.await_args_list]
        assert messages == [
            "Deleted the trailers of 1.",
            "Error deleting trailer!",
            "Deleted the trailers of 3.",
        ]

"""Add Search YouTube to profiles (Phase 9)

A profile searches YouTube when no known video suits it, as every
profile did before. The new flag lets a person turn that off: the
profile then takes known videos only and waits for TMDB. It starts off
for a profile of another type than Trailer, because a search result is
not checked against TMDB (decision 5 of Phase 9, as amended on Oct 8,
2026).

Revision ID: d4e6f1a7b3c5
Revises: c3d8e5f9a2b1
Create Date: 2026-10-08 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e6f1a7b3c5'
down_revision: Union[str, None] = 'c3d8e5f9a2b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "search_youtube",
                sa.Boolean(),
                server_default="1",
                nullable=False,
            )
        )
    # A profile of another type than Trailer starts without the search.
    op.execute(
        "UPDATE trailerprofile SET search_youtube = 0, always_search = 0"
        " WHERE video_type != 'trailer'"
    )

    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    op.execute("PRAGMA foreign_keys=OFF")

    with op.batch_alter_table("trailerprofile", schema=None) as batch_op:
        batch_op.drop_column("search_youtube")

    op.execute("PRAGMA foreign_keys=ON")

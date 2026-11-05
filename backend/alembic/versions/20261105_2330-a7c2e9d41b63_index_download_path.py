"""Index the path of download (#733)

The restore of a deleted download checks, under the write lock, that no
active download has its path. The disk scan checks the same before it
records a new file. Without an index, each check read the whole table. A
Cleanup Task that restores every download after a network share came back
then ran one full read of the table for each download.

The index is created without a batch operation, so SQLite does not copy
the table.

Revision ID: a7c2e9d41b63
Revises: f295ffc28658
Create Date: 2026-11-05 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a7c2e9d41b63'
down_revision: Union[str, None] = 'f295ffc28658'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_download_path", "download", ["path"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_download_path", table_name="download")

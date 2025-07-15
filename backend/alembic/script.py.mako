"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
import sqlmodel.sql.sqltypes
from app_logger import ModuleLogger
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}

logger = ModuleLogger("AlembicMigrations")


def upgrade() -> None:
    # Disable foreign keys temporarily for migrations
    op.execute("PRAGMA foreign_keys=OFF")

    ${upgrades if upgrades else "pass"}
    
    # Re-enable foreign keys after migrations
    op.execute("PRAGMA foreign_keys=ON")


def downgrade() -> None:
    # Disable foreign keys temporarily for migrations
    op.execute("PRAGMA foreign_keys=OFF")
    
    ${downgrades if downgrades else "pass"}

    # Re-enable foreign keys after migrations
    op.execute("PRAGMA foreign_keys=ON")

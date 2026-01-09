from datetime import datetime, timezone
from enum import Enum

from pydantic import field_validator
from sqlmodel import Field, Relationship

from core.base.database.models.base import AppSQLModel


def get_current_time():
    return datetime.now(timezone.utc)


class FileFolderType(Enum):
    """Type of File/Folder Info. \n"""

    FILE = "file"
    FOLDER = "folder"
    SYMLINK = "symlink"

    def __lt__(self, other: "FileFolderType") -> bool:
        # Sort order: folder < symlink < file
        type_values = {"file": 2, "folder": 1, "symlink": 1}
        if self.value not in type_values or other.value not in type_values:
            # If either type is not in the type_values, fallback to string comparison
            return self.value < other.value
        return type_values[self.value] < type_values[other.value]


class FileFolderInfoBase(AppSQLModel):
    """
    Base model for FileFolderInfo.\n
    Note: \n
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨 \n
    👉Use :class:`FileFolderInfo` for working with database.👈 \n
    👉Use :class:`FileFolderInfoCreate` to create/update file/folder info.👈 \n
    👉Use :class:`FileFolderInfoRead` to read the data. 👈 \n
    """

    type: FileFolderType
    name: str
    size: int  # Size in bytes
    path: str
    is_trailer: bool = False
    modified: datetime

    def __lt__(self, other: "FileFolderInfoBase") -> bool:
        # Folders come before files; if same type, sort by name
        if self.type != other.type:
            return self.type < other.type
        return self.name.lower() < other.name.lower()


class FileFolderInfo(FileFolderInfoBase, table=True):
    """
    Database model for FileFolderInfo.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    👉Use :class:`FileFolderInfoCreate` to create/update file/folder info.👈 \n
    👉Use :class:`FileFolderInfoRead` to read the data. 👈 \n
    """

    id: int | None = Field(default=None, primary_key=True)
    media_id: int = Field(foreign_key="media.id", ondelete="CASCADE")
    parent_id: int | None = Field(
        foreign_key="filefolderinfo.id", default=None, nullable=True
    )
    children: list["FileFolderInfo"] = Relationship(cascade_delete=True)

    @field_validator("modified", mode="after")
    @classmethod
    def set_timezone_to_utc(cls, value: datetime) -> datetime:
        return value.astimezone(timezone.utc)


class FileFolderInfoCreate(FileFolderInfoBase):
    """
    Model for creating/updating FileFolderInfo.
    """

    id: int | None = None
    media_id: int
    parent_id: int | None = None
    children: list["FileFolderInfoCreate"] = []


class FileFolderInfoRead(FileFolderInfoBase):
    """
    Model for reading FileFolderInfo from database.
    """

    id: int
    media_id: int
    parent_id: int | None = None
    children: list["FileFolderInfoRead"] = []

    @field_validator("modified", mode="after")
    @classmethod
    def correct_timezone(cls, value: datetime) -> datetime:
        return cls.set_timezone_to_utc(value)

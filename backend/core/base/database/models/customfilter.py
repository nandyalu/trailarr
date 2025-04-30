from enum import Enum
from sqlmodel import Field, Relationship, SQLModel

# if TYPE_CHECKING:
from core.base.database.models.filter import (
    Filter,
    FilterCreate,
    FilterRead,
)

# from core.base.database.models.trailerprofile import (
#     TrailerProfile,
#     TrailerProfileCreate,
# )


class FilterType(Enum):
    HOME = "HOME"
    """For Home CustomFilter"""
    MOVIES = "MOVIES"
    """For Movies CustomFilter"""
    SERIES = "SERIES"
    """For Series CustomFilter"""
    TRAILER = "TRAILER"
    """Only for Trailer Profiles"""


class _CustomFilterBase(SQLModel):
    """
    Base model for CustomFilter.\n
    Note: \n
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨 \n
    👉Use :class:`CustomFilter for working with database.👈 \n
    """

    filter_name: str
    filter_type: FilterType = Field(default=FilterType.TRAILER)
    """Type of custom filter:
        - `Home`: Home view
        - `Movies`: Movies view
        - `Series`: Series view
        - `Trailer`: Trailer view"""


class CustomFilter(_CustomFilterBase, table=True):
    """
    Database model for CustomFilter.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    👉Use :class:`CustomFilterCreate` to create/update view filters.👈 \n
    👉Use :class:`CustomFilterRead` to read the data.👈
    """

    id: int | None = Field(default=None, primary_key=True)
    # filters: list["Filter"] = Relationship(back_populates="customfilter")
    filters: list[Filter] = Relationship()
    """List of filters for the view"""
    # trailerprofile: Optional["TrailerProfile"] = Relationship(
    #     back_populates="customfilter"
    # )


class CustomFilterCreate(_CustomFilterBase):
    """
    Model for creating/updating CustomFilter.
    - Leave `trailerprofile_id` and `trailerprofile` as `None` for page\
        view filters.
    """

    id: int | None = None
    filters: list[FilterCreate] = []
    """List of filters for the view"""
    # trailerprofile: Optional["TrailerProfileCreate"] = None


class CustomFilterRead(_CustomFilterBase):
    """
    Model for reading CustomFilter.
    """

    id: int
    filters: list[FilterRead]
    """List of filters for the view"""

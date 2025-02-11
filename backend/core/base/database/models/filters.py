from enum import Enum
from sqlmodel import Field, Relationship, SQLModel


class FilterCondition(Enum):
    EQUAL = "EQUAL"
    """Value Equal to"""
    NOT_EQUAL = "NOT_EQUAL"
    """Value Not Equal to"""
    GREATER_THAN = "GREATER_THAN"
    """Value Greater than"""
    GREATER_THAN_EQUAL = "GREATER_THAN_EQUAL"
    """Value Greater than or equal to"""
    LESS_THAN = "LESS_THAN"
    """Value Less than"""
    LESS_THAN_EQUAL = "LESS_THAN_EQUAL"
    """Value Less than or equal to"""
    IN = "IN"
    """Value in a list"""
    NOT_IN = "NOT_IN"
    """Value not in a list"""
    IS_NULL = "IS_NULL"
    """Value is null"""
    IS_NOT_NULL = "IS_NOT_NULL"
    """Value is not null"""
    STARTSWITH = "STARTSWITH"
    """Value starts with"""
    ENDSWITH = "ENDSWITH"
    """Value ends with"""
    CONTAINS = "CONTAINS"
    """Value contains"""
    NOT_CONTAINS = "NOT_CONTAINS"
    """Value does not contain"""


class _FilterBase(SQLModel):
    """
    Base model for Filter.\n
    Note: \n
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨 \n
    👉Use :class:`Filter` for working with database.👈 \n
    👉Use :class:`FilterCreate` to create/update filters.👈 \n
    👉Use :class:`FilterRead` to read the data.👈
    """

    filter_by: str
    """Column name to filter by"""
    filter_condition: FilterCondition
    """Filter condition"""
    filter_value: str
    """Value to filter by"""


class Filter(_FilterBase, table=True):
    """
    Database model for Filter.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    👉Use :class:`FilterCreate` to create/update filters.👈 \n
    👉Use :class:`FilterRead` to read the data.👈
    """

    id: int | None = Field(default=None, primary_key=True)

    viewfilter_id: int | None = Field(default=None, foreign_key="viewfilter.id")
    viewfilter: "ViewFilter" = Relationship(back_populates="filters")


class FilterCreate(_FilterBase):
    """
    Model for creating/updating Filter.
    """

    id: int | None = None
    viewfilter_id: int | None = None
    viewfilter: "ViewFilter | None" = None


class FilterRead(_FilterBase):
    """
    Model for reading Filter.
    """

    id: int
    viewfilter_id: int


class _ViewFilterBase(SQLModel):
    """
    Base model for ViewFilter.\n
    Note: \n
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨 \n
    👉Use :class:`ViewFilter for working with database.👈 \n
    """

    view_name: str
    """Name of the view
    `Home`: Home view
    `Movies`: Movies view
    `Series`: Series view
    `Trailer`: Trailer view"""


class ViewFilter(_ViewFilterBase, table=True):
    """
    Database model for ViewFilter.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    👉Use :class:`ViewFilterCreate` to create/update view filters.👈 \n
    👉Use :class:`ViewFilterRead` to read the data.👈
    """

    id: int | None = Field(default=None, primary_key=True)
    filters: list[Filter] = Relationship(back_populates="viewfilter")
    """List of filters for the view"""


class ViewFilterCreate(_ViewFilterBase):
    """
    Model for creating/updating ViewFilter.
    """

    id: int | None = None
    filters: list[FilterCreate] = []
    """List of filters for the view"""


class ViewFilterRead(_ViewFilterBase):
    """
    Model for reading ViewFilter.
    """

    id: int
    filters: list[FilterRead]
    """List of filters for the view"""

from enum import Enum
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from core.base.database.models.customfilter import (
        CustomFilter,
        CustomFilterCreate,
    )


class FilterCondition(Enum):
    # Boolean conditions
    # IS_TRUE = "IS_TRUE"
    # IS_FALSE = "IS_FALSE"
    EQUALS = "EQUALS"

    # Date conditions
    IS_AFTER = "IS_AFTER"
    IS_BEFORE = "IS_BEFORE"
    IN_THE_LAST = "IN_THE_LAST"
    NOT_IN_THE_LAST = "NOT_IN_THE_LAST"
    # EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"

    # Number conditions
    GREATER_THAN = "GREATER_THAN"
    GREATER_THAN_EQUAL = "GREATER_THAN_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_THAN_EQUAL = "LESS_THAN_EQUAL"
    # EQUALS = 'EQUALS',
    # NOT_EQUALS= 'NOT_EQUALS',

    # String conditions
    CONTAINS = "CONTAINS"
    NOT_CONTAINS = "NOT_CONTAINS"
    # EQUALS = 'EQUALS',
    # NOT_EQUALS= 'NOT_EQUALS',
    STARTS_WITH = "STARTS_WITH"
    NOT_STARTS_WITH = "NOT_STARTS_WITH"
    ENDS_WITH = "ENDS_WITH"
    NOT_ENDS_WITH = "NOT_ENDS_WITH"
    IS_EMPTY = "IS_EMPTY"
    IS_NOT_EMPTY = "IS_NOT_EMPTY"


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

    customfilter_id: int | None = Field(
        default=None, foreign_key="customfilter.id"
    )
    customfilter: "CustomFilter" = Relationship(back_populates="filters")


class FilterCreate(_FilterBase):
    """
    Model for creating/updating Filter.
    """

    id: int | None = None
    customfilter_id: int | None = None
    customfilter: Optional["CustomFilterCreate"] = None


class FilterRead(_FilterBase):
    """
    Model for reading Filter.
    """

    id: int
    customfilter_id: int

from enum import Enum
from typing import Self

from pydantic import field_validator, model_validator
from sqlmodel import Field, SQLModel


class FilterCondition(Enum):
    # Boolean conditions
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


BOOL_COLS = [
    "is_movie",
    "media_exists",
    "trailer_exists",
    "monitor",
    "arr_monitored",
]
INT_COLS = ["id", "connection_id", "arr_id", "year", "runtime"]
STR_COLS = [
    "title",
    "clean_title",
    "language",
    "studio",
    "media_filename",
    "youtube_trailer_id",
    "folder_path",
    "imdb_id",
    "txdb_id",
    "title_slug",
    "status",
]
DATE_COLS = ["added_at", "updated_at", "downloaded_at"]

ALL_COLS = BOOL_COLS + INT_COLS + STR_COLS + DATE_COLS


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

    @field_validator("filter_by", mode="after")
    @classmethod
    def validate_filter_by(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("filter_by cannot be empty or whitespace.")
        if value not in ALL_COLS:
            raise ValueError(
                f"Invalid filter_by value: {value}. "
                f"Valid values are: {ALL_COLS}"
            )
        return value

    @model_validator(mode="after")
    def validate_filter_condition_for_filter_by(self) -> Self:
        filter_by = self.filter_by
        filter_condition = self.filter_condition
        filter_value = self.filter_value
        # Boolean conditions
        if filter_by in BOOL_COLS:
            if filter_condition != FilterCondition.EQUALS:
                raise ValueError(
                    f"Invalid filter_condition for {filter_by}:"
                    f" {filter_condition}. Valid value: EQUALS"
                )
            if filter_value.lower() not in ["true", "false"]:
                raise ValueError(
                    f"Invalid filter_value for {filter_by}: {filter_value}. "
                    "Valid values are: true, false"
                )
            return self
        # Integer conditions
        if filter_by in INT_COLS:
            if filter_condition not in [
                FilterCondition.GREATER_THAN,
                FilterCondition.GREATER_THAN_EQUAL,
                FilterCondition.LESS_THAN,
                FilterCondition.LESS_THAN_EQUAL,
                FilterCondition.EQUALS,
                FilterCondition.NOT_EQUALS,
            ]:
                raise ValueError(
                    f"Invalid filter_condition for {filter_by}:"
                    f" {filter_condition}. Valid values: "
                    "GREATER_THAN, GREATER_THAN_EQUAL, LESS_THAN, "
                    "LESS_THAN_EQUAL, EQUALS, NOT_EQUALS"
                )
            try:
                int(filter_value)
            except ValueError:
                raise ValueError(
                    f"Invalid filter_value for {filter_by}: {filter_value}. "
                    "Must be an integer."
                )
            return self
        # String conditions
        if filter_by in STR_COLS:
            if filter_condition not in [
                FilterCondition.EQUALS,
                FilterCondition.NOT_EQUALS,
                FilterCondition.CONTAINS,
                FilterCondition.NOT_CONTAINS,
                FilterCondition.STARTS_WITH,
                FilterCondition.NOT_STARTS_WITH,
                FilterCondition.ENDS_WITH,
                FilterCondition.NOT_ENDS_WITH,
                FilterCondition.IS_EMPTY,
                FilterCondition.IS_NOT_EMPTY,
            ]:
                raise ValueError(
                    f"Invalid filter_condition for {filter_by}:"
                    f" {filter_condition}. Valid values: "
                    "EQUALS, NOT_EQUALS, CONTAINS, NOT_CONTAINS, "
                    "STARTS_WITH, NOT_STARTS_WITH, ENDS_WITH, "
                    "NOT_ENDS_WITH, IS_EMPTY, IS_NOT_EMPTY"
                )
            return self
        # Date conditions
        if filter_by in DATE_COLS:
            if filter_condition not in [
                FilterCondition.IS_AFTER,
                FilterCondition.IS_BEFORE,
                FilterCondition.IN_THE_LAST,
                FilterCondition.NOT_IN_THE_LAST,
                FilterCondition.EQUALS,
                FilterCondition.NOT_EQUALS,
            ]:
                raise ValueError(
                    f"Invalid filter_condition for {filter_by}:"
                    f" {filter_condition}. Valid values: "
                    "IS_AFTER, IS_BEFORE, IN_THE_LAST, NOT_IN_THE_LAST"
                )
            if filter_condition in [
                FilterCondition.IN_THE_LAST,
                FilterCondition.NOT_IN_THE_LAST,
            ]:
                try:
                    int(filter_value)
                except ValueError:
                    raise ValueError(
                        f"Invalid filter_value for {filter_by}:"
                        f" {filter_value}. Must be an integer."
                    )
                if int(filter_value) <= 0:
                    raise ValueError(
                        f"Invalid filter_value for {filter_by}:"
                        f" {filter_value}. Must be a positive integer."
                    )
                return self
            if filter_condition in [
                FilterCondition.IS_AFTER,
                FilterCondition.IS_BEFORE,
                FilterCondition.EQUALS,
                FilterCondition.NOT_EQUALS,
            ]:
                if not isinstance(filter_value, str):
                    raise ValueError(
                        f"Invalid filter_value for {filter_by}:"
                        f" {filter_value}. Must be a date string."
                    )
                if not filter_value:
                    raise ValueError(
                        f"Invalid filter_value for {filter_by}:"
                        f" {filter_value}. Must be a non-empty date string."
                    )
            try:
                # Assuming filter_value is a date string
                from datetime import datetime

                datetime.strptime(filter_value, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Invalid filter_value for {filter_by}: {filter_value}. "
                    "Must be a date string in YYYY-MM-DD format."
                )
        return self


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
    # customfilter: "CustomFilter" = Relationship(back_populates="filters")


class FilterCreate(_FilterBase):
    """
    Model for creating/updating Filter.
    """

    id: int | None = None
    customfilter_id: int | None = None
    # customfilter: Optional["CustomFilterCreate"] = None


class FilterRead(_FilterBase):
    """
    Model for reading Filter.
    """

    id: int
    customfilter_id: int

from enum import Enum
from typing import Any
from sqlmodel import Field, Relationship

from core.base.database.models.base import AppSQLModel

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


class _CustomFilterBase(AppSQLModel):
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
    filters: list[Filter] = Relationship(cascade_delete=True)
    """List of filters for the view"""
    # trailerprofile: Optional["TrailerProfile"] = Relationship(
    #     back_populates="customfilter"
    # )

    # @classmethod
    # def from_create(cls, obj: "CustomFilterCreate") -> "CustomFilter":
    #     """
    #     Convert CustomFilterCreate to CustomFilter.
    #     This method is used to convert the CustomFilterCreate model
    #     to the CustomFilter model for database operations.
    #     """
    #     _filters = [Filter.model_validate(f) for f in obj.filters]
    #     obj.filters = _filters  # type: ignore[assignment]
    #     # Validate the CustomFilterCreate model
    #     _validated_obj = cls.model_validate(obj.model_dump())
    #     _validated_obj.filters = _filters
    #     return _validated_obj

    # # Overriding the model_validate method to ensure
    # # that the Filters are validated correctly.
    # # This is necessary because the CustomFilter has nested models.
    @classmethod
    def model_validate(
        cls,
        obj: "CustomFilter | CustomFilterCreate | CustomFilterRead | dict[str, Any]",
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, Any] | None = None,
        update: dict[str, Any] | None = None,
    ) -> "CustomFilter":
        """
        Validate the CustomFilter model. \n
        This method ensures that the nested models are validated
        correctly before validating the CustomFilter itself.
        """
        if isinstance(obj, dict):
            # If obj is a dict, convert it to CustomFilterCreate
            obj = CustomFilterCreate.model_validate(obj)
        db_filters: list[Filter] = []
        if isinstance(obj, cls):
            # If obj is already a CustomFilter instance, return it
            db_filters = obj.filters
        else:
            db_filters = [Filter.model_validate(f) for f in obj.filters]
        _validated_obj = super().model_validate(
            obj.model_dump(),
            strict=strict,
            from_attributes=from_attributes,
            context=context,
            update=update,
        )
        _validated_obj.filters = db_filters
        return _validated_obj


class CustomFilterCreate(_CustomFilterBase):
    """
    Model for creating/updating CustomFilter.
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

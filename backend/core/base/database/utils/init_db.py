from sqlmodel import SQLModel

# !!! IMPORTANT !!!
# Import all the models that are used in the application so that \
# SQLModel can create the tables
from core.base.database.models.connection import Connection  # noqa: F401
from core.base.database.models.media import Media  # noqa: F401
from core.base.database.models.filter import Filter  # noqa: F401
from core.base.database.models.customfilter import CustomFilter  # noqa: F401
from core.base.database.models.trailerprofile import (  # noqa: F401
    TrailerProfile,
)  # noqa: F401

# from core.base.database.models.filter import (
#     Filter,
#     FilterCreate,
#     FilterRead,
# )
# from core.base.database.models.customfilter import (
#     CustomFilter,
#     CustomFilterCreate,
#     CustomFilterRead,
# )
# from core.base.database.models.trailerprofile import (
#     TrailerProfile,
#     TrailerProfileCreate,
#     TrailerProfileRead,
# )

# !!! IMPORTANT !!!
# Rebuild models that have relationships after importing all models
# Filter.model_rebuild()
# FilterCreate.model_rebuild()
# FilterRead.model_rebuild()
# CustomFilter.model_rebuild()
# CustomFilterCreate.model_rebuild()
# CustomFilterRead.model_rebuild()
# TrailerProfile.model_rebuild()
# TrailerProfileCreate.model_rebuild()
# TrailerProfileRead.model_rebuild()

from core.base.database.utils.engine import engine  # noqa: E402

#  make sure all SQLModel models are imported (database.models) before\
# initializing DB. Otherwise, SQLModel might fail to initialize \
# relationships properly


def init_db():
    """Initialize the database and creates tables for SQLModels."""
    # Create the database tables
    SQLModel.metadata.create_all(bind=engine)

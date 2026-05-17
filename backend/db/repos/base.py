from sqlmodel import Session
from exceptions import ItemNotFoundError


def get_or_404(session: Session, model_class, id: int):
    """Fetch a row by primary key or raise ItemNotFoundError."""
    obj = session.get(model_class, id)
    if obj is None:
        raise ItemNotFoundError(model_name=model_class.__name__, id=id)
    return obj

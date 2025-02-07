from fastapi import APIRouter

from api.v1.models import SearchMedia
from core.base.database.manager.base import MediaDatabaseManager


search_router = APIRouter(prefix="/search", tags=["Search"], deprecated=True)


@search_router.get("/{query}")
async def search_media(query: str) -> list[SearchMedia]:
    db_handler = MediaDatabaseManager()
    media_list = db_handler.search(query)
    search_media_list: list[SearchMedia] = []
    for media in media_list:
        media_data = media.model_dump()
        search_media = SearchMedia.model_validate(media_data)
        search_media_list.append(search_media)
    return search_media_list

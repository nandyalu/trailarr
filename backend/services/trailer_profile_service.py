"""Trailer profile service — CRUD + MediaTrailerStatus row sync.

After every profile create/update/setting-change, we re-evaluate which media
items match the profile's filters and ensure the status table is in sync:
- Matching media → create PENDING rows if they don't already exist.
- Non-matching media → delete rows that have no linked download.
"""
from app_logger import ModuleLogger
import db.repos.media as media_repo
import db.repos.trailer_profile as profile_repo
import db.repos.trailer_status as status_repo
from db.models.trailerprofile import TrailerProfileCreate, TrailerProfileRead
from utils.filters import matches_filters

logger = ModuleLogger("TrailerProfileService")


def _sync_status_rows(profile: TrailerProfileRead) -> None:
    all_media = media_repo.read_all(movies_only=profile.for_movies)
    filters = profile.customfilter.filters

    matching = [m for m in all_media if matches_filters(m, filters)]
    non_matching_ids = [m.id for m in all_media if not matches_filters(m, filters)]

    if matching:
        created = status_repo.create_rows_for_profile(
            profile_id=profile.id,
            for_movies=profile.for_movies,
            max_count=profile.max_count,
            download_season_videos=profile.download_season_videos,
            media_list=matching,
        )
        if created:
            logger.info(
                f"Profile '{profile.customfilter.filter_name}': created {created} new status row(s)."
            )

    if non_matching_ids:
        deleted = status_repo.delete_undownloaded_rows_for_profile(
            profile_id=profile.id,
            media_ids=non_matching_ids,
        )
        if deleted:
            logger.info(
                f"Profile '{profile.customfilter.filter_name}': deleted {deleted} undownloaded row(s)."
            )


def create(profile_create: TrailerProfileCreate) -> TrailerProfileRead:
    profile = profile_repo.create(profile_create)
    _sync_status_rows(profile)
    return profile


def read(profile_id: int) -> TrailerProfileRead:
    return profile_repo.read(profile_id)


def read_all() -> list[TrailerProfileRead]:
    return profile_repo.read_all()


def update(profile_id: int, profile_create: TrailerProfileCreate) -> TrailerProfileRead:
    profile = profile_repo.update(profile_id, profile_create)
    _sync_status_rows(profile)
    return profile


def update_setting(profile_id: int, setting: str, value: str | int | bool) -> TrailerProfileRead:
    profile = profile_repo.update_setting(profile_id, setting, value)
    _sync_status_rows(profile)
    return profile


def delete(profile_id: int) -> bool:
    return profile_repo.delete(profile_id)

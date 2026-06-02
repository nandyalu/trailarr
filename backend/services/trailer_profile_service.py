"""Trailer profile service — CRUD pass-through to profile_repo."""

import db.repos.trailer_profile as profile_repo
from db.models.trailerprofile import TrailerProfileCreate, TrailerProfileRead


def create(profile_create: TrailerProfileCreate) -> TrailerProfileRead:
    return profile_repo.create(profile_create)


def read(profile_id: int) -> TrailerProfileRead:
    return profile_repo.read(profile_id)


def read_all() -> list[TrailerProfileRead]:
    return profile_repo.read_all()


def update(profile_id: int, profile_create: TrailerProfileCreate) -> TrailerProfileRead:
    return profile_repo.update(profile_id, profile_create)


def update_setting(profile_id: int, setting: str, value: str | int | bool) -> TrailerProfileRead:
    return profile_repo.update_setting(profile_id, setting, value)


def delete(profile_id: int) -> bool:
    return profile_repo.delete(profile_id)

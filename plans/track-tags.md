# Parallel Track — Media Tags

**Status:** not started · **Releases:** Stage 1 targets v0.14.x, Stage 2 ships with
Phase 10 (v0.15.0) · **Depends on:** Phase 6 (filter editor + virtual-field validation,
shipped v0.11.3); Stage 2 wants Phase 10's profile rework

Raised by [#491](https://github.com/nandyalu/trailarr/issues/491): a user reviewing every
trailer in their library has no way to record which ones they have already been through.
Their follow-up asked for bulk tag and untag.

## Objective

Give users a place to record what they know about their own media, and let both views and
profiles act on it. Tags are **user-owned state** under cross-phase invariant 6 — no
background task ever writes, relabels or deletes one.

## Stage 1 — Tags, view filtering, bulk tag/untag (v0.14.x)

Independent of Phases 9 and 10. Rides infrastructure that already shipped.

- `tag` and `media_tag` tables + migration; CRUD API; tag manager in Settings.
- A `tags` filter field with `CONTAINS` / `NOT_CONTAINS` / `IS_EMPTY`, in the Media group
  of the Phase 6 filter editor, with a tag picker rather than free text.
- Tag and untag in the existing `batch_update_media` bulk handler — the requester's
  follow-up, and close to free once the endpoint exists.
- Tag chips on the media card and details page.

**If you touch `batch_update_media`, fix H15 while you are in there** — a failing batch
delete currently tells the user twice.

## Stage 2 — Tags in profile filters (with Phase 10, v0.15.0)

"Apply this profile only to media tagged X." This is the version people actually want,
and it is what makes tags worth the schema.

Phase 6 made the downloads and files fields **view-only**, because a profile filtering on
its own outputs is circular. **That argument does not apply to tags**: a tag is user
input, not an output of the download engine, so a TRAILER-type filter may read it without
any feedback loop. State this explicitly in the validation code next to the
`VIRTUAL_DOWNLOAD_COLS` rejection, or someone will "fix" it by rejecting tags too.

Ships with Phase 10 because that release reworks profiles anyway (movie/series
classification + presets), so the profile-editor work overlaps.

## Settled decision — Arr tags are a separate, read-only field

Radarr and Sonarr have their own tags, and users will expect Trailarr to show them.
They **cannot share a field with Trailarr tags.** Under invariant 6 an Arr tag is
sync-derived and automation-owned, so the next poll would overwrite the user's own
"Reviewed" tag — the pre-roadmap `monitor` flag, repeated.

The shape, if and when it is built: a separate `arr_tags` field, written only by the Arr
sync, filterable, never editable in Trailarr, displayed differently from user tags.
Stage 2 at the earliest; post-v1.0 is fine. Recording it here is the point — this is
exactly the feature that gets improvised into the wrong field by someone being helpful.

## Wargame

- W1. A tag is deleted while filters reference it: the filter matches nothing and the
  editor shows the tag as deleted. Same resolution as Phase 6's W2 for deleted profiles.
- W2. Bulk tag over a 3,000-item selection: one request, not 3,000. The batch handler
  already takes a list of ids.
- W3. Media removed from Arr and demoted to Plex-only keeps its tags — the row survives
  the demotion, and tags belong to the user, not to the connection.
- W4. Media deleted outright: `media_tag` rows go with it (cascade), the `tag` stays.
- W5. Two tags differing only in case, or in leading/trailing space. Decide at creation —
  normalize and match case-insensitively — rather than leaving two "reviewed" tags.
- W6. Stage 2 only: every media matched by a profile through a tag the user later removes
  simply stops matching. Nothing is deleted, and already-downloaded trailers stay.

## Docs to update

- New tags page under `docs/user-guide/library/` (or the filters page, if it stays
  small): creating tags, tagging in bulk, filtering by tag.
- `docs/user-guide/settings/profiles/filters.md` — the `tags` field, and at Stage 2 the
  fact that profile filters accept it while downloads/files fields stay view-only, with
  the reason.
- `docs/user-guide/settings/profiles/examples.md` — one recipe at Stage 2
  ("only download trailers for media tagged `favourites`").

## Exit criteria

Stage 1: a user can tag a selection in bulk, filter a view to that tag, and rename or
delete the tag without breaking the view. Stage 2: a profile restricted to a tag
downloads for exactly the tagged media, and the Phase 3 matrix explains the skip for the
rest.

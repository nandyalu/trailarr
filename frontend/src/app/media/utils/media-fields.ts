import {Download, Media} from 'src/app/models/media';
import {bytesToSize, durationString, durationStringSeconds} from 'src/util';

/**
 * The one registry of the fields that the Expanded view and the Table view
 * can show (Phase 9, decision 11). The Configure Fields dialog, the table
 * header and the expanded card all read this list. A media field reads the
 * media item. A trailer field reads one active download row.
 *
 * The keys are stored in localStorage (`TrailarrExpandedFields`,
 * `TrailarrTableColumns`). Do not rename a key: a saved key that the
 * registry no longer knows is ignored, not thrown.
 */

/** How many trailers one card or one table cell shows before `+N more`. */
export const MAX_TRAILERS_PER_CARD = 3;

/** The text for an empty cell. */
export const EMPTY_VALUE = '—';

export type FieldGroup = 'media' | 'trailer';
export type FieldView = 'expanded' | 'table';

/** Data the trailer fields need beyond the download row. */
export interface FieldContext {
  /** Profile id -> profile name, from `ProfileService.allProfiles`. */
  profileNames: ReadonlyMap<number, string>;
}

interface BaseFieldDef {
  key: string;
  /** The label in the Configure Fields dialog. A trailer label has no
   * `Trailer` prefix: the dialog shows it under the Trailers heading. */
  label: string;
  group: FieldGroup;
  /** The views that offer the field. Both when not set. */
  views?: readonly FieldView[];
}

export interface MediaFieldDef extends BaseFieldDef {
  group: 'media';
  /** Text for a table cell. `null` shows a dash. Not set for a date field. */
  value?: (media: Media) => string | null;
  /** The date for a date field. The template formats it with the DatePipe,
   * so the viewer's timezone setting applies. `null` shows a dash. */
  date?: (media: Media) => Date | null;
  /** Text for the expanded tag when it differs from `value`. `null` hides
   * the tag. */
  tag?: (media: Media) => string | null;
  /** A prefix for the expanded tag: `IMDB: tt0123`. */
  tagPrefix?: string;
  /** A long path: the expanded tag clips it and shows the full text on hover. */
  path?: boolean;
}

export interface TrailerFieldDef extends BaseFieldDef {
  group: 'trailer';
  /** Text for one active download row. */
  value: (download: Download, context: FieldContext) => string;
  /** When set, the field shows one value for the media item, not one line
   * per trailer, and the cap does not apply (the trailer count). */
  summary?: (block: TrailerBlock) => string;
}

export type FieldDef = MediaFieldDef | TrailerFieldDef;

/** The dialog shows the fields in groups with one heading each. */
export interface FieldOptionGroup {
  label: string;
  options: {key: string; label: string}[];
}

/** The active trailers of one media item, in the order every cell shares. */
export interface TrailerBlock {
  /** The trailers a card or cell shows, newest first, at most
   * `MAX_TRAILERS_PER_CARD`. */
  shown: Download[];
  /** How many active trailers the cap hides. */
  more: number;
  /** All active trailers, for the count field. */
  count: number;
}

const yesNo = (value: boolean): string => (value ? 'Yes' : 'No');
const text = (value: string | null | undefined): string | null => value || null;

export const MEDIA_FIELDS: readonly MediaFieldDef[] = [
  {key: 'year', label: 'Year', group: 'media', value: (m) => (m.year ? String(m.year) : null)},
  {key: 'overview', label: 'Overview', group: 'media', views: ['expanded'], value: (m) => text(m.overview)},
  {key: 'status', label: 'Status', group: 'media', value: (m) => (m.status ? m.status.charAt(0).toUpperCase() + m.status.slice(1) : null), tag: (m) => m.status},
  {key: 'runtime', label: 'Runtime', group: 'media', value: (m) => (m.runtime ? durationString(m.runtime) : null)},
  {key: 'language', label: 'Language', group: 'media', value: (m) => text(m.language)},
  {key: 'studio', label: 'Studio', group: 'media', value: (m) => text(m.studio)},
  {
    key: 'season_count',
    label: 'Season Count',
    group: 'media',
    value: (m) => (m.is_movie || !m.season_count ? null : String(m.season_count)),
    tag: (m) => (m.is_movie || !m.season_count ? null : `${m.season_count} Season${m.season_count !== 1 ? 's' : ''}`),
  },
  {key: 'monitor', label: 'Monitored', group: 'media', value: (m) => yesNo(m.monitor), tag: (m) => (m.monitor ? 'Monitored' : 'Unmonitored')},
  {key: 'arr_monitored', label: 'Arr Monitored', group: 'media', value: (m) => yesNo(m.arr_monitored), tag: (m) => `Arr: ${m.arr_monitored ? 'Monitored' : 'Unmonitored'}`},
  {key: 'media_exists', label: 'Media Exists', group: 'media', value: (m) => yesNo(m.media_exists), tagPrefix: 'Media'},
  {key: 'imdb_id', label: 'IMDB ID', group: 'media', value: (m) => text(m.imdb_id), tagPrefix: 'IMDB'},
  {key: 'txdb_id', label: 'TVDB/TMDB ID', group: 'media', value: (m) => text(m.txdb_id), tagPrefix: 'TVDB/TMDB'},
  {key: 'folder_path', label: 'Folder Path', group: 'media', value: (m) => text(m.folder_path), path: true},
  {key: 'media_filename', label: 'Filename', group: 'media', value: (m) => text(m.media_filename), path: true},
  {key: 'added_at', label: 'Date Added', group: 'media', date: (m) => m.added_at, tagPrefix: 'Added'},
  {key: 'updated_at', label: 'Date Updated', group: 'media', date: (m) => m.updated_at, tagPrefix: 'Updated'},
  {key: 'downloaded_at', label: 'Date Downloaded', group: 'media', date: (m) => m.downloaded_at, tagPrefix: 'Downloaded'},
  {key: 'plex_rating_key', label: 'Plex Rating Key', group: 'media', value: (m) => text(m.plex_rating_key), tagPrefix: 'Plex Key'},
  {
    key: 'plex_trailer',
    label: 'Plex Trailer',
    group: 'media',
    value: (m) => (m.plex_trailer === null ? null : yesNo(m.plex_trailer)),
    tag: (m) => `Plex Trailer: ${yesNo(Boolean(m.plex_trailer))}`,
  },
];

/**
 * The name of a trailer profile. `Unknown` when the download has no profile
 * (id 0). `Deleted [id]` when the profile is gone (Phase 6 W2).
 */
export function profileName(profileId: number, context: FieldContext): string {
  if (!profileId) return 'Unknown';
  return context.profileNames.get(profileId) ?? `Deleted [${profileId}]`;
}

/** The keys reuse the Phase 6 virtual-filter names, so a filter and a
 * column share one vocabulary. */
export const TRAILER_FIELDS: readonly TrailerFieldDef[] = [
  {key: 'download_video_type', label: 'Type', group: 'trailer', value: (d) => d.video_type || 'trailer'},
  {key: 'download_resolution', label: 'Resolution', group: 'trailer', value: (d) => (d.resolution ? `${d.resolution}p` : EMPTY_VALUE)},
  {key: 'download_video_codec', label: 'Video Codec', group: 'trailer', value: (d) => d.video_format || EMPTY_VALUE},
  {key: 'download_audio_codec', label: 'Audio Codec', group: 'trailer', value: (d) => d.audio_format || EMPTY_VALUE},
  {key: 'download_audio_language', label: 'Audio Language', group: 'trailer', value: (d) => d.audio_language || EMPTY_VALUE},
  {
    key: 'download_subtitles',
    label: 'Subtitles',
    group: 'trailer',
    value: (d) => (d.subtitle_format ? `${d.subtitle_format}${d.subtitle_language ? ` (${d.subtitle_language})` : ''}` : EMPTY_VALUE),
  },
  {key: 'download_container', label: 'Container', group: 'trailer', value: (d) => d.file_format || EMPTY_VALUE},
  {key: 'download_duration', label: 'Duration', group: 'trailer', value: (d) => (d.duration ? durationStringSeconds(d.duration) : EMPTY_VALUE)},
  {key: 'download_size', label: 'Size', group: 'trailer', value: (d) => (d.size ? bytesToSize(d.size) : EMPTY_VALUE)},
  {key: 'download_profile', label: 'Profile', group: 'trailer', value: (d, context) => profileName(d.profile_id, context)},
  {key: 'download_count', label: 'Count', group: 'trailer', value: () => EMPTY_VALUE, summary: (block) => String(block.count)},
];

export const ALL_FIELDS: readonly FieldDef[] = [...MEDIA_FIELDS, ...TRAILER_FIELDS];

const FIELDS_BY_KEY: ReadonlyMap<string, FieldDef> = new Map(ALL_FIELDS.map((field) => [field.key, field]));

export function isTrailerField(field: FieldDef): field is TrailerFieldDef {
  return field.group === 'trailer';
}

/** The label a table header shows: a trailer field carries the `Trailer` prefix. */
export function headerLabel(field: FieldDef): string {
  return isTrailerField(field) ? `Trailer ${field.label}` : field.label;
}

function offeredIn(field: FieldDef, view: FieldView): boolean {
  return !field.views || field.views.includes(view);
}

/** The fields a view offers, in registry order. */
export function fieldsForView(view: FieldView): FieldDef[] {
  return ALL_FIELDS.filter((field) => offeredIn(field, view));
}

/** The Configure Fields dialog groups: **Media**, then **Trailers**. */
export function fieldOptionGroups(view: FieldView): FieldOptionGroup[] {
  const fields = fieldsForView(view);
  const options = (group: FieldGroup) => fields.filter((f) => f.group === group).map(({key, label}) => ({key, label}));
  return [
    {label: 'Media', options: options('media')},
    {label: 'Trailers', options: options('trailer')},
  ];
}

/**
 * The field definitions for a list of saved keys, in the saved order. A key
 * the registry does not know, or that the view does not offer, is dropped.
 */
export function resolveFields(keys: readonly string[], view: FieldView): FieldDef[] {
  const resolved: FieldDef[] = [];
  for (const key of keys) {
    const field = FIELDS_BY_KEY.get(key);
    if (field && offeredIn(field, view)) resolved.push(field);
  }
  return resolved;
}

/**
 * The active download rows of a media item: `file_exists` only, the same
 * rows `applyDownloadFilter` reads, so a filter and a cell never disagree.
 * Newest first, by `added_at` (when Trailarr downloaded the trailer).
 */
export function activeTrailers(media: Media): Download[] {
  const time = (d: Download) => new Date(d.added_at).getTime() || 0;
  return media.downloads.filter((d) => d.file_exists).sort((a, b) => time(b) - time(a));
}

/** One shared order per media item, computed once and read by every cell. */
export function buildTrailerBlock(media: Media): TrailerBlock {
  const active = activeTrailers(media);
  return {
    shown: active.slice(0, MAX_TRAILERS_PER_CARD),
    more: Math.max(0, active.length - MAX_TRAILERS_PER_CARD),
    count: active.length,
  };
}

/** The text of one trailer field for one media item: the summary for a
 * summary field, else one line per shown trailer. */
export function trailerCellLines(field: TrailerFieldDef, block: TrailerBlock, context: FieldContext): string[] {
  if (field.summary) return [field.summary(block)];
  return block.shown.map((d) => field.value(d, context));
}

/** The text of a media field for a table cell. A date field is formatted in
 * the template; this returns `null` for it. */
export function mediaCellValue(field: MediaFieldDef, media: Media): string | null {
  return field.value ? field.value(media) : null;
}

/** The text of a media field for an expanded tag. `null` hides the tag. */
export function mediaTagValue(field: MediaFieldDef, media: Media): string | null {
  if (field.tag) return field.tag(media);
  const value = field.value ? field.value(media) : null;
  if (value === null) return null;
  return field.tagPrefix ? `${field.tagPrefix}: ${value}` : value;
}

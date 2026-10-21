import {CustomFilter, CustomFilterCreate} from './customfilter';

/** The kinds of video a profile can download. Mirrors `VideoType` in
 * backend/database/models/video_type.py: the values are what the database
 * stores, the labels are what a person reads. */
export const DEFAULT_VIDEO_TYPE = 'trailer';

export const VIDEO_TYPE_LABELS: Record<string, string> = {
  trailer: 'Trailer',
  teaser: 'Teaser',
  clip: 'Clip',
  featurette: 'Featurette',
  behind_the_scenes: 'Behind the Scenes',
  bloopers: 'Bloopers',
  other: 'Other',
};

/** The stored values, in the order the UI offers them. */
export const VIDEO_TYPES: string[] = Object.keys(VIDEO_TYPE_LABELS);

/** `{value, label}` pairs for a select or a radio bar. */
export const VIDEO_TYPE_OPTIONS: {value: string; label: string}[] = VIDEO_TYPES.map((value) => ({value, label: VIDEO_TYPE_LABELS[value]}));

/** The label of a type. An empty or missing value is a trailer; an unknown
 * value reads as 'Other', as `video_type_label` does in the backend. */
export function videoTypeLabel(value: string | null | undefined): string {
  const normalized = (value ?? '').trim().toLowerCase() || DEFAULT_VIDEO_TYPE;
  return VIDEO_TYPE_LABELS[normalized] ?? 'Other';
}

/** True for the trailer type, the only type that can search YouTube. An
 * empty or missing value is a trailer. */
export function isTrailerType(value: string | null | undefined): boolean {
  return ((value ?? '').trim().toLowerCase() || DEFAULT_VIDEO_TYPE) === DEFAULT_VIDEO_TYPE;
}

export interface TrailerProfileRead {
  id: number;
  customfilter_id: number;
  customfilter: CustomFilter;
  enabled?: boolean;
  priority?: number;
  retry_count?: number;
  file_format?: string;
  file_name?: string;
  folder_enabled?: boolean;
  folder_name?: string;
  embed_metadata?: boolean;
  remove_silence?: boolean;
  audio_format?: string;
  audio_volume_level?: number;
  video_format?: string;
  video_resolution?: number;
  language?: string;
  subtitles_enabled?: boolean;
  subtitles_auto_generated?: boolean;
  subtitles_format?: string;
  subtitles_language?: string;
  search_query?: string;
  search_youtube?: boolean;
  min_duration?: number;
  max_duration?: number;
  always_search?: boolean;
  /** The kind of video this profile downloads: 'trailer' (default), 'teaser', ...
   * (Phase 9). Every type except 'trailer' comes from TMDB only. */
  video_type?: string;
  upgrade_to_tmdb?: boolean;
  delete_replaced_trailer?: boolean;
  replace_unknown_videos?: boolean;
  exclude_words?: string;
  include_words?: string;
  uploader_ids?: string;
  ytdlp_extra_options?: string;
  /** Deprecated (Phase 4): no longer honored or shown in the UI; column drops in Phase 5. */
  custom_folder?: string;
  notify_plex?: boolean;
  skip_if_plex_trailer?: boolean;
  skip_if_plex_trailer_resolution?: number;
}

export interface TrailerProfileCreate {
  id?: number | null;
  customfilter_id?: number | null;
  customfilter: CustomFilterCreate;
  enabled?: boolean;
  priority?: number;
  retry_count?: number;
  file_format?: string;
  file_name?: string;
  folder_enabled?: boolean;
  folder_name?: string;
  embed_metadata?: boolean;
  remove_silence?: boolean;
  audio_format?: string;
  audio_volume_level?: number;
  video_format?: string;
  video_resolution?: number;
  language?: string;
  subtitles_enabled?: boolean;
  subtitles_auto_generated?: boolean;
  subtitles_format?: string;
  subtitles_language?: string;
  search_query?: string;
  search_youtube?: boolean;
  min_duration?: number;
  max_duration?: number;
  always_search?: boolean;
  /** The kind of video this profile downloads: 'trailer' (default), 'teaser', ...
   * (Phase 9). Every type except 'trailer' comes from TMDB only. */
  video_type?: string;
  upgrade_to_tmdb?: boolean;
  delete_replaced_trailer?: boolean;
  replace_unknown_videos?: boolean;
  exclude_words?: string;
  include_words?: string;
  uploader_ids?: string;
  ytdlp_extra_options?: string;
  /** Deprecated (Phase 4): no longer honored or shown in the UI; column drops in Phase 5. */
  custom_folder?: string;
  notify_plex?: boolean;
  skip_if_plex_trailer?: boolean;
  skip_if_plex_trailer_resolution?: number;
}

export type VideoIdSource = 'arr' | 'tmdb' | 'user';

export interface VideoId {
  id: number;
  media_id: number;
  youtube_id: string;
  video_type: string;
  source: VideoIdSource;
  language: string;
  season: number;
  created_at: string;
  updated_at: string;
}

export interface VideoIdCreate {
  video_type: string;
  language: string;
  youtube_id: string;
}

export const VIDEO_TYPE_OPTIONS: string[] = [
  'trailer',
  'teaser',
  'clip',
  'behind the scenes',
  'bloopers',
  'featurette',
  'opening credits',
  'other',
];

export const SOURCE_LABELS: Record<VideoIdSource, string> = {
  arr: 'Arr',
  tmdb: 'TMDB',
  user: 'You',
};

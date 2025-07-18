export interface Download {
  id: number;
  path: string;
  file_name: string;
  size: number;
  updated_at: Date;
  resolution: string;
  video_format: string;
  audio_format: string;
  audio_channels: string;
  file_format: string;
  duration: number;
  subtitles: string;
  added_at: Date;
  profile_id: number;
  media_id: number;
  youtube_id: string;
  file_exists: boolean;
}

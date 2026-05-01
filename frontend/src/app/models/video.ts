export interface StreamInfo {
  index: number;
  codec_name: string;
  codec_type: string;
  language?: string;
  audio_channels?: number;
  coded_height?: number;
  coded_width?: number;
  duration?: string;
  sample_rate?: number;
}

export interface VideoInfo {
  file_path: string;
  name: string;
  format_name: string;
  created_at: string;
  updated_at: string;
  streams: StreamInfo[];
  bitrate?: string;
  duration?: string;
  duration_seconds?: number;
  size?: number;
  youtube_channel?: string;
  youtube_id?: string | null;
}

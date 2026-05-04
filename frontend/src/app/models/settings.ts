export interface Settings {
  api_key: string;
  app_data_dir: string;
  app_mode: string;
  app_theme: string;
  delete_corrupted_trailers: boolean;
  delete_trailer_connection: boolean;
  files_full_scan: boolean;
  delete_trailer_media: boolean;
  ffmpeg_timeout: number;
  gpu_available_amd: boolean;
  gpu_available_intel: boolean;
  gpu_available_nvidia: boolean;
  gpu_enabled_amd: boolean;
  gpu_enabled_intel: boolean;
  gpu_enabled_nvidia: boolean;
  log_level: string;
  monitor_enabled: boolean;
  monitor_interval: number;
  server_hostname: string;
  server_model: string;
  server_platform: string;
  server_platform_version: string;
  server_start_time: string;
  timezone: string;
  update_available: boolean;
  update_available_ytdlp: boolean;
  update_ytdlp: boolean;
  url_base: string;
  version: string;
  wait_for_media: boolean;
  webui_disable_auth: boolean;
  webui_username: string;
  yt_cookies_path: string;
  ytdlp_version: string;
}

export interface ServerStats {
  movies_count: number;
  movies_monitored: number;
  series_count: number;
  series_monitored: number;
  trailers_detected: number;
  trailers_downloaded: number;
}

export interface FolderInfo {
  created: string;
  files?: FolderInfo[];
  name: string;
  path: string;
  size?: string;
  type?: string;
}

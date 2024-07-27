export interface Settings {
    api_key: string
    version: string
    server_start_time: string
    timezone: string
    debug: boolean
    monitor_enabled: boolean
    monitor_interval: number
    trailer_folder_movie: boolean
    trailer_folder_series: boolean
    trailer_resolution: number
    trailer_audio_format: string
    trailer_video_format: string
    trailer_subtitles_enabled: boolean
    trailer_subtitles_format: string
    trailer_subtitles_language: string
    trailer_file_format: string
    trailer_embed_metadata: boolean
    trailer_remove_sponsorblocks: boolean
    trailer_web_optimized: boolean
}

export interface ServerStats {
    trailers_downloaded: number
    movies_count: number
    series_count: number
    monitored_count: number
}
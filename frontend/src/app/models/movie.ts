export interface Movie {
    connection_id: number;
    arr_id: number;
    title: string;
    year: number;
    language: string;
    overview: string;
    runtime: number;
    youtube_trailer_id: string;
    folder_path: string;
    imdb_id: string;
    txdb_id: string;
    poster_url: string;
    fanart_url: string;
    poster_path: string;
    fanart_path: string;
    trailer_exists: boolean;
    monitor: boolean;
    arr_monitored: boolean;
    id: number;
    added_at: Date;
    updated_at: Date;
    downloaded_at: Date;
}

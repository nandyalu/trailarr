import { DatePipe } from "@angular/common";

export interface Media {
    is_movie: boolean;
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

export function mapMedia(media: any, is_movie: boolean): Media {
    return {
        ...media,
        is_movie: is_movie,
        added_at: new DatePipe('en-US').transform(media.added_at, 'medium'),
        updated_at: new DatePipe('en-US').transform(media.updated_at, 'medium'),
        downloaded_at: new DatePipe('en-US').transform(media.downloaded_at, 'medium')
    };
}

export interface SearchMedia {
    id: number;
    title: string;
    year: number;
    youtube_trailer_id: string;
    imdb_id: string;
    txdb_id: string;
    is_movie: boolean;
}

export interface FolderInfo {
    type: string;
    name: string;
    size: string;
    files: FolderInfo[];
    modified: Date;
}

export function mapFolderInfo(folder: any): FolderInfo {
    return {
        ...folder,
        isExpanded: false,
        modified: new DatePipe('en-US').transform(folder.created, 'medium'),
        files: folder.files.map((file: any) => isFile(file) ? mapFileInfo(file) : mapFolderInfo(file))
    };
}

function mapFileInfo(file: any): FolderInfo {
    return {
      ...file,
      modified: new DatePipe('en-US').transform(file.created, 'medium')
    };
}

function isFile(file: any): boolean {
    // Implement this function based on how you differentiate between a file and a folder in your data.
    // For example, you might check a 'type' property:
    return file.type === 'file';
}
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
    status: string;
    id: number;
    added_at: Date;
    updated_at: Date;
    downloaded_at: Date;

    // Additional properties
    isImageLoaded: boolean;
}

export function mapMedia(media: any): Media {
    return {
        ...media,
        added_at: new DatePipe('en-US').transform(media.added_at, 'medium'),
        updated_at: new DatePipe('en-US').transform(media.updated_at, 'medium'),
        downloaded_at: new DatePipe('en-US').transform(media.downloaded_at, 'medium'),
        isImageLoaded: false
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
    poster_path: string | null;
}

export interface FolderInfo {
    type: string;
    name: string;
    size: string;
    path: string;
    files: FolderInfo[];
    modified: Date;
    isExpanded: boolean;
}

export function mapFolderInfo(folder: any): FolderInfo {
    let _files = [{
        type: 'folder', name: 'None', size: '', path: '',
        files: [], modified: new Date(), isExpanded: false
    }];
    if (folder.files) {
        _files = folder.files.map((file: any) => isFile(file) ? mapFileInfo(file) : mapFolderInfo(file));
    }
    return {
        ...folder,
        isExpanded: false,
        modified: new DatePipe('en-US').transform(folder.created, 'medium'),
        files: _files
    };
}

function mapFileInfo(file: any): FolderInfo {
    return {
        ...file,
        isExpanded: false,
        modified: new DatePipe('en-US').transform(file.created, 'medium')
    };
}

function isFile(file: any): boolean {
    // Implement this function based on how you differentiate between a file and a folder in your data.
    // For example, you might check a 'type' property:
    return file.type === 'file';
}
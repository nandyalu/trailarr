import {FileFolderInfo} from './filefolderinfo';
import {buildTrailerStatusMap, computeMonitorStatus, MediaTrailerStatus} from './mediatrailerstatus';

export interface Download {
  id: number;
  path: string;
  file_name: string;
  file_hash: string;
  size: number;
  resolution: number; // e.g., 1080, 2160
  file_format: string; // e.g., "mp4", "mkv"
  video_format: string; // e.g., "h264", "h265"
  audio_format: string; // e.g., "aac", "ac3"
  audio_language: string | null; // e.g., "eng", "tel"
  subtitle_format: string | null; // e.g., "srt", "ass"
  subtitle_language: string | null; // e.g., "eng"
  duration: number; // in seconds
  youtube_id: string;
  youtube_channel: string;
  file_exists: boolean;
  video_type: string; // e.g., "trailer", "teaser", "featurette", "other"
  profile_id: number; // ID of the TrailerProfile used
  media_id: number;
  added_at: Date; // When trailer was downloaded
  updated_at: Date; // When file was last modified
}

export function parseDate(dateStr: string): Date | null {
  if (!dateStr) {
    return null; // Return epoch if dateStr is empty or invalid
  }
  if (dateStr.endsWith('Z')) {
    return new Date(dateStr);
  }
  return new Date(`${dateStr}Z`);
}

export function mapDownload(download: any): Download {
  return {
    ...download,
    file_exists: Boolean(download.file_exists),
    added_at: parseDate(download.added_at),
    updated_at: parseDate(download.updated_at),
  };
}

export {buildTrailerStatusMap} from './mediatrailerstatus';

/** Returns true if any download has file_exists=true AND video_type='trailer'. */
export function computeTrailerExists(downloads: Download[]): boolean {
  return downloads.some((d) => d.file_exists && d.video_type === 'trailer');
}

export function buildDownloadMap(downloads: Download[]): Map<number, Download[]> {
  const downloadMap = new Map<number, Download[]>();

  // Group downloads by media_id
  downloads.forEach((download) => {
    if (!downloadMap.has(download.media_id)) {
      downloadMap.set(download.media_id, []);
    }
    downloadMap.get(download.media_id)!.push(download);
  });

  return downloadMap;
}

export interface Media {
  is_movie: boolean;
  connection_id: number;
  arr_id: number;
  title: string;
  clean_title: string;
  year: number;
  language: string;
  studio: string;
  media_exists: boolean;
  media_filename: string;
  season_count: number;
  overview: string;
  runtime: number;
  youtube_trailer_id: string;
  folder_path: string;
  imdb_id: string;
  txdb_id: string;
  title_slug: string;
  poster_url: string;
  fanart_url: string;
  poster_path: string;
  fanart_path: string;
  monitor: boolean;
  arr_monitored: boolean;
  id: number;
  added_at: Date;
  updated_at: Date;
  downloaded_at: Date;
  downloads: Download[];
  files: FileFolderInfo | null;
  trailer_statuses: MediaTrailerStatus[];
  // Computed locally from trailer_statuses — not sent by backend
  trailer_exists: boolean;
  status: string;

  plex_rating_key: string | null;
  plex_connection_id: number | null;
  plex_trailer: boolean | null;

  // Additional properties
  isImageLoaded: boolean;
}

export function mapMedia(media: any): Media {
  const downloads: Download[] = (media.downloads || []).map(mapDownload);
  const trailerExists = computeTrailerExists(downloads);
  return {
    ...media,
    is_movie: Boolean(media.is_movie),
    media_exists: Boolean(media.media_exists),
    monitor: Boolean(media.monitor),
    arr_monitored: Boolean(media.arr_monitored),
    added_at: parseDate(media.added_at),
    updated_at: parseDate(media.updated_at),
    downloaded_at: parseDate(media.downloaded_at),
    downloads,
    trailer_statuses: [],
    trailer_exists: trailerExists,
    status: trailerExists ? 'downloaded' : (media.monitor ? 'monitored' : 'missing'),
    isImageLoaded: false,
  };
}

/** Re-compute the derived trailer_exists and status fields when trailer_statuses arrive. */
export function applyTrailerStatuses(media: Media, statuses: MediaTrailerStatus[]): Media {
  const trailerExists = computeTrailerExists(media.downloads);
  return {
    ...media,
    trailer_statuses: statuses,
    trailer_exists: trailerExists,
    status: computeMonitorStatus(statuses, trailerExists, media.monitor),
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
  let _files = [
    {
      type: 'folder',
      name: 'None',
      size: '',
      path: '',
      files: [],
      modified: new Date(),
      isExpanded: false,
    },
  ];
  if (folder.files) {
    _files = folder.files.map((file: any) => (isFile(file) ? mapFileInfo(file) : mapFolderInfo(file)));
  }
  return {
    ...folder,
    isExpanded: false,
    modified: new Date(`${folder.created}`),
    files: _files,
  };
}

function mapFileInfo(file: any): FolderInfo {
  return {
    ...file,
    isExpanded: false,
    modified: new Date(`${file.created}`),
  };
}

function isFile(file: any): boolean {
  // Implement this function based on how you differentiate between a file and a folder in your data.
  // For example, you might check a 'type' property:
  return file.type === 'file';
}

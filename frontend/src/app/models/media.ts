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
  profile_id: number; // ID of the TrailerProfile used
  media_id: number;
  added_at: Date; // When trailer was downloaded
  updated_at: Date; // When file was last modified
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
  trailer_exists: boolean;
  monitor: boolean;
  arr_monitored: boolean;
  status: string;
  id: number;
  added_at: Date;
  updated_at: Date;
  downloaded_at: Date;
  downloads: Download[];

  // Additional properties
  isImageLoaded: boolean;
}

export function mapMedia(media: any): Media {
  return {
    ...media,
    added_at: new Date(`${media.added_at}Z`),
    updated_at: new Date(`${media.updated_at}Z`),
    downloaded_at: new Date(`${media.downloaded_at}Z`),
    isImageLoaded: false,
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
    modified: new Date(`${folder.created}Z`),
    files: _files,
  };
}

function mapFileInfo(file: any): FolderInfo {
  return {
    ...file,
    isExpanded: false,
    modified: new Date(`${file.created}Z`),
  };
}

function isFile(file: any): boolean {
  // Implement this function based on how you differentiate between a file and a folder in your data.
  // For example, you might check a 'type' property:
  return file.type === 'file';
}

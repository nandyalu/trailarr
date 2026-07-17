export interface PathMapping {
  id: number | null;
  connection_id: number | null;
  path_to: string;
  path_from: string;
}

export interface PathMappingCreate {
  id: number | null;
  connection_id: number | null;
  path_to: string;
  path_from: string;
}

export enum ArrType {
  Radarr = 'radarr',
  Sonarr = 'sonarr',
  Plex = 'plex',
}

export interface Connection {
  name: string;
  arr_type: ArrType;
  url: string;
  external_url: string;
  api_key: string;
  monitor_new_media: boolean;
  id: number;
  added_at: Date;
  machine_identifier: string | null;
  path_mappings: PathMapping[];
}

export interface ConnectionCreate {
  name: string;
  arr_type: ArrType;
  url: string;
  external_url: string;
  api_key: string;
  monitor_new_media: boolean;
  path_mappings: PathMappingCreate[];
}

export interface ConnectionRead {
  added_at: string;
  api_key: string;
  arr_type: ArrType;
  id: number;
  monitor_new_media: boolean;
  name: string;
  machine_identifier: string | null;
  path_mappings: PathMappingCreate[];
  url: string;
  external_url: string;
}

export interface ConnectionUpdate {
  name: string;
  arr_type: ArrType;
  url: string;
  external_url: string;
  api_key: string;
  monitor_new_media: boolean;
  // id: number;
  path_mappings: PathMappingCreate[];
}

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
}

export enum MonitorType {
  Missing = 'missing',
  New = 'new',
  None = 'none',
  Sync = 'sync',
}

export interface Connection {
  name: string;
  arr_type: ArrType;
  url: string;
  external_url: string;
  api_key: string;
  monitor: MonitorType;
  id: number;
  added_at: Date;
  path_mappings: PathMapping[];
}

export interface ConnectionCreate {
  name: string;
  arr_type: ArrType;
  url: string;
  external_url: string;
  api_key: string;
  monitor: MonitorType;
  path_mappings: PathMappingCreate[];
}

export interface ConnectionRead {
  added_at: string;
  api_key: string;
  arr_type: ArrType;
  id: number;
  monitor: MonitorType;
  name: string;
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
  monitor: MonitorType;
  // id: number;
  path_mappings: PathMappingCreate[];
}

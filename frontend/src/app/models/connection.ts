export interface PathMapping {
  id: number | null;
  connection_id: number | null;
  path_to: string;
  path_from: string;
}

export interface PathMappingCreate {
  path_to: string;
  path_from: string;
}

export interface Connection {
  name: string;
  arr_type: string;
  url: string;
  api_key: string;
  monitor: string;
  id: number;
  added_at: Date;
  path_mappings: PathMapping[];
}

export interface ConnectionCreate {
  name: string;
  arr_type: string;
  url: string;
  api_key: string;
  monitor: string;
  path_mappings: PathMappingCreate[];
}

export interface ConnectionUpdate {
  name: string;
  arr_type: string;
  url: string;
  api_key: string;
  monitor: string;
  id: number;
  path_mappings: PathMapping[];
}

export interface Connection {
    name: string;
    arr_type: string;
    url: string;
    api_key: string;
    monitor: string;
    id: number;
    added_at: Date;
}

export interface ConnectionCreate {
    name: string;
    arr_type: string;
    url: string;
    api_key: string;
    monitor: string;
}

export interface ConnectionUpdate {
    name: string;
    arr_type: string;
    url: string;
    api_key: string;
    monitor: string;
    id: number;
}
export interface Logs {
    datetime: string;
    level: string;
    filename: string;
    lineno: number;
    module: string;
    message: string;
    raw_log: string;
}
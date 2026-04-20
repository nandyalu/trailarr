export interface Logs {
  datetime: string;
  level: string;
  filename: string;
  lineno: number;
  module: string;
  message: string;
  raw_log: string;
}

export enum LogLevel {
  Trace = 'TRACE',
  Debug = 'DEBUG',
  Info = 'INFO',
  Warning = 'WARNING',
  Error = 'ERROR',
  Exception = 'EXCEPTION',
  Critical = 'CRITICAL',
}

export interface AppLogRecord {
  id: number;
  created: string;
  level: LogLevel;
  filename: string;
  lineno: number;
  loggername: string;
  message: string;
  mediaid: number | null;
  taskname: string | null;
  traceback: string | null;
}

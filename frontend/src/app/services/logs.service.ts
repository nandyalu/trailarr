import {HttpClient} from '@angular/common/http';
import {inject, Injectable} from '@angular/core';
import {environment} from '../../environment';
import {AppLogRecord, Logs} from '../models/logs';

@Injectable({providedIn: 'root'})
export class LogsService {
  private readonly http = inject(HttpClient);

  readonly logsUrl = `${environment.apiUrl}${environment.logs}` as const;

  downloadLogs = () => this.http.get(this.logsUrl + 'download', {responseType: 'blob'});
  getLogs = () => this.http.get<Logs[]>(this.logsUrl);

  getRawLogs = () => this.http.get<AppLogRecord[]>(this.logsUrl + 'raw');
}

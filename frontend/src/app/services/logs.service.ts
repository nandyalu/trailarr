import {HttpClient} from '@angular/common/http';
import {inject, Injectable} from '@angular/core';
import {AppLogRecord} from 'generated-sources/openapi';
import {environment} from '../../environment';
import {Logs} from '../models/logs';

@Injectable({providedIn: 'root'})
export class LogsService {
  private readonly http = inject(HttpClient);

  readonly logsUrl = `${environment.apiUrl}${environment.logs}` as const;

  downloadLogs = () => this.http.get(this.logsUrl + 'download', {responseType: 'blob'});
  getLogs = () => this.http.get<Logs[]>(this.logsUrl);

  getRawLogs = () => this.http.get<AppLogRecord[]>(this.logsUrl + 'raw');
}

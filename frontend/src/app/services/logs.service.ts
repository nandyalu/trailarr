import {HttpClient} from '@angular/common/http';
import {inject, Injectable} from '@angular/core';
import {environment} from '../../environment';
import {Logs} from '../models/logs';

@Injectable({providedIn: 'root'})
export class LogsService {
  private readonly http = inject(HttpClient);

  private readonly logsUrl = environment.apiUrl + environment.logs;

  downloadLogs = () => this.http.get(this.logsUrl + 'download', {responseType: 'blob'});
  getLogs = () => this.http.get<Logs[]>(this.logsUrl);
}

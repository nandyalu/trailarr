import {HttpClient} from '@angular/common/http';
import {inject, Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {environment} from '../../environment';
import {Logs} from '../models/logs';

@Injectable({
  providedIn: 'root',
})
export class LogsService {
  private http = inject(HttpClient);

  private logsUrl = environment.apiUrl + environment.logs;

  getLogs(): Observable<Logs[]> {
    return this.http.get<Logs[]>(this.logsUrl);
  }

  downloadLogs(): Observable<Blob> {
    return this.http.get(this.logsUrl + 'download', {responseType: 'blob'});
  }
}

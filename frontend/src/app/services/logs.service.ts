import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environment';
import { Logs } from '../models/logs';

@Injectable({
  providedIn: 'root'
})
export class LogsService {

  private logsUrl = environment.apiUrl + environment.logs;

  constructor(private http: HttpClient) { }

  getLogs(): Observable<Logs[]> {
    return this.http.get<Logs[]>(this.logsUrl);
  }

  downloadLogs(): Observable<Blob> {
    return this.http.get(this.logsUrl + 'download', { responseType: 'blob' });
  }
}

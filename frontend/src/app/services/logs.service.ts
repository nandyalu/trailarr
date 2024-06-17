import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environment';

@Injectable({
  providedIn: 'root'
})
export class LogsService {

  private logsUrl = environment.apiUrl + environment.logs;

  constructor(private http: HttpClient) { }

  getLogs(): Observable<string[]> {
    return this.http.get<string[]>(this.logsUrl);
  }
}

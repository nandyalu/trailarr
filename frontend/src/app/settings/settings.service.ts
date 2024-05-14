import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, catchError, map, of } from 'rxjs';
import { environment } from '../../environment';
import { Connection, ConnectionCreate, ConnectionUpdate } from '../models/connection';

@Injectable({
  providedIn: 'root'
})
export class SettingsService {
  private settingsUrl = environment.apiUrl + environment.settings;

  constructor(private http: HttpClient) { }

  getSettings(): Observable<any> {
    return this.http.get<any>(this.settingsUrl);
  }

  private connectionsUrl = environment.apiUrl + environment.connections;
  getConnections(): Observable<Connection[]> {
    return this.http.get<Connection[]>(this.connectionsUrl).pipe(
      map((connections: any[]) => connections.map(connection => ({
        ...connection,
        added_at: new Date(connection.added_at)
      })))
    );
  }

  getConnection(id: number): Observable<Connection> {
    var connectionIdUrl = this.connectionsUrl + id;
    return this.http.get<Connection>(connectionIdUrl).pipe(
      map((connection: any) => ({
        ...connection,
        added_at: new Date(connection.added_at)
      }))
    );
  }

  addConnection(connection: ConnectionCreate): Observable<string> {
    return this.http.post<string>(this.connectionsUrl, connection).pipe(
      catchError((error: any) => {
        let errorMessage = '';
        if (error.error instanceof ErrorEvent) {
          // client-side error
          errorMessage = `Error: ${error.error.message}`;
        } else {
          // server-side error
          errorMessage = `Error: ${error.status} ${error.error.detail}`;
        }
        return of(errorMessage);
       })
    );
  }

  updateConnection(connection: ConnectionUpdate): Observable<string> {
    var connectionIdUrl = this.connectionsUrl + connection.id;
    return this.http.put<string>(connectionIdUrl, connection).pipe(
      catchError((error: any) => {
        let errorMessage = '';
        if (error.error instanceof ErrorEvent) {
          // client-side error
          errorMessage = `Error: ${error.error.message}`;
        } else {
          // server-side error
          errorMessage = `Error: ${error.status} ${error.error.detail}`;
        }
        return of(errorMessage);
       })
    );
  }

  deleteConnection(id: number): Observable<string> {
    var connectionIdUrl = this.connectionsUrl + id;
    return this.http.delete<string>(connectionIdUrl).pipe(
      catchError((error: any) => {
        let errorMessage = '';
        if (error.error instanceof ErrorEvent) {
          // client-side error
          errorMessage = `Error: ${error.error.message}`;
        } else {
          // server-side error
          errorMessage = `Error: ${error.status} ${error.error.detail}`;
        }
        return of(errorMessage);
       })
    );
  }
}
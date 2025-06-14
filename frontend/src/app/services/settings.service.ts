import {HttpClient, httpResource} from '@angular/common/http';
import {inject, Injectable, signal} from '@angular/core';
import {FolderInfo} from 'generated-sources/openapi';
import {catchError, map, Observable, of} from 'rxjs';
import {environment} from '../../environment';
import {Connection, ConnectionCreate, ConnectionUpdate} from '../models/connection';
import {ServerStats, Settings} from '../models/settings';

@Injectable({
  providedIn: 'root',
})
export class SettingsService {
  private readonly http = inject(HttpClient);

  private connectionsUrl = environment.apiUrl + environment.connections;
  private settingsUrl = environment.apiUrl + environment.settings;
  private filesUrl = environment.apiUrl + environment.files;

  readonly settingsResource = httpResource<Settings>(() => this.settingsUrl);
  readonly filesPath = signal<string>('');
  readonly filesResource = httpResource<FolderInfo[]>(
    () => {
      return {
        url: this.filesUrl + 'files_simple',
        params: {
          path: this.filesPath(),
        },
      };
    },
    {
      defaultValue: [],
    },
  );
  readonly connectionsResource = httpResource<Connection[]>(() => ({url: this.connectionsUrl}), {
    defaultValue: [],
  });

  getServerStats(): Observable<ServerStats> {
    var serverStatsUrl = this.settingsUrl + 'stats';
    return this.http.get<any>(serverStatsUrl);
  }

  updateSetting(key: string, value: any): Observable<string> {
    const updateSettingUrl = this.settingsUrl + 'update';
    // Ensure empty strings are sent as a single space to avoid issues with empty values
    if (typeof value === 'string' && value === '') value = ' ';
    const update_obj = {
      key: key,
      value: value,
    };
    return this.http.put<string>(updateSettingUrl, update_obj).pipe(
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
      }),
    );
  }

  updatePassword(currentPassword: string, newUsername: string, newPassword: string): Observable<string> {
    const updatePasswordUrl = this.settingsUrl + 'updatelogin';
    const update_obj = {
      current_password: currentPassword,
      new_username: newUsername,
      new_password: newPassword,
    };
    return this.http.put<string>(updatePasswordUrl, update_obj).pipe(
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
      }),
    );
  }

  getConnection(id: number): Observable<Connection> {
    var connectionIdUrl = this.connectionsUrl + id;
    return this.http.get<Connection>(connectionIdUrl).pipe(
      map((connection: any) => ({
        ...connection,
        added_at: new Date(connection.added_at),
      })),
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
      }),
    );
  }

  testConnection(connection: ConnectionCreate): Observable<string> {
    var testConnectionUrl = this.connectionsUrl + 'test';
    return this.http.post<string>(testConnectionUrl, connection).pipe(
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
      }),
    );
  }

  getRootFolders(connection: ConnectionCreate): Observable<string[] | string> {
    var rootFoldersUrl = this.connectionsUrl + 'rootfolders';
    return this.http.post<string[]>(rootFoldersUrl, connection).pipe(
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
      }),
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
      }),
    );
  }
}

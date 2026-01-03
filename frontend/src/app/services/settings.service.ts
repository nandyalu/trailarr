import {HttpClient, httpResource} from '@angular/common/http';
import {inject, Injectable, signal} from '@angular/core';
import {FolderInfo, ServerStats, Settings} from 'generated-sources/openapi';
import {catchError, Observable, of} from 'rxjs';
import {environment} from '../../environment';

@Injectable({
  providedIn: 'root',
})
export class SettingsService {
  private readonly http = inject(HttpClient);

  private settingsUrl = environment.apiUrl + environment.settings;
  private filesUrl = environment.apiUrl + environment.files;

  readonly settingsResource = httpResource<Settings>(() => this.settingsUrl);
  readonly filesPath = signal<string>('');
  readonly filesResource = httpResource<FolderInfo[]>(
    () => {
      const path = this.filesPath();
      if (!path) {
        return undefined;
      }
      return {
        url: this.filesUrl + 'files_simple',
        params: {
          path: path,
        },
      };
    },
    {
      defaultValue: [],
    },
  );

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

  logout(): Observable<string> {
    const logoutUrl = this.settingsUrl + 'logout';
    return this.http.post<string>(logoutUrl, {});
  }
}

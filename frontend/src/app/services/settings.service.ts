import {HttpClient, httpResource} from '@angular/common/http';
import {computed, inject, Injectable, signal} from '@angular/core';
import {catchError, Observable, of} from 'rxjs';
import {FolderInfo, ServerStats, Settings} from '../models/settings';
import {environment} from '../../environment';

@Injectable({
  providedIn: 'root',
})
export class SettingsService {
  private readonly http = inject(HttpClient);

  private settingsUrl = environment.apiUrl + environment.settings;
  private filesUrl = environment.apiUrl + environment.files;

  readonly settingsResource = httpResource<Settings>(() => this.settingsUrl);

  /** Settings, or undefined while loading or after a failed request.
   *
   * Read THIS in effects, computeds, and templates — never
   * `settingsResource.value()` directly. A resource in the error state
   * throws from `value()`; thrown inside change detection, that error
   * halts all rendering (a fresh session whose first `/settings/` call
   * races auth and gets a 401 froze the whole app this way). */
  readonly settings = computed<Settings | undefined>(() => (this.settingsResource.hasValue() ? this.settingsResource.value() : undefined));
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

}

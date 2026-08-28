import {HttpClient, httpResource} from '@angular/common/http';
import {inject, Injectable} from '@angular/core';
import {catchError, Observable} from 'rxjs';
import {CookiesStatus, HealthCheckResult, HealthReport} from 'src/app/models/health';
import {environment} from 'src/environment';
import {handleError} from './utils';

@Injectable({
  providedIn: 'root',
})
export class HealthService {
  private readonly http = inject(HttpClient);

  private healthUrl = environment.apiUrl + 'health/';

  /** Cached system health report (the backend re-runs it when stale). */
  readonly reportResource = httpResource<HealthReport | null>(() => ({url: this.healthUrl + 'checks'}), {
    defaultValue: null,
  });

  /** Cookies file status — never contains cookie values. */
  readonly cookiesResource = httpResource<CookiesStatus | null>(() => ({url: this.healthUrl + 'cookies'}), {
    defaultValue: null,
  });

  runChecks(): Observable<HealthReport> {
    return this.http.post<HealthReport>(this.healthUrl + 'checks/run', {}).pipe(catchError(handleError()));
  }

  runYtdlpTest(force = false): Observable<HealthCheckResult> {
    return this.http.post<HealthCheckResult>(`${this.healthUrl}checks/ytdlp-test?force=${force}`, {}).pipe(catchError(handleError()));
  }

  uploadCookies(content: string): Observable<CookiesStatus> {
    return this.http.post<CookiesStatus>(this.healthUrl + 'cookies', {content}).pipe(catchError(handleError()));
  }

  deleteCookies(): Observable<CookiesStatus> {
    return this.http.delete<CookiesStatus>(this.healthUrl + 'cookies').pipe(catchError(handleError()));
  }
}

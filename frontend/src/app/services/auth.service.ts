import {HttpClient} from '@angular/common/http';
import {inject, Injectable, signal} from '@angular/core';
import {catchError, map, Observable, of, tap} from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly http = inject(HttpClient);

  private readonly authUrl = 'api/v1/auth/';
  private readonly CACHE_TTL = 60_000; // 60 seconds

  readonly isAuthenticated = signal(false);
  private _lastChecked = 0;

  login(username: string, password: string): Observable<void> {
    return this.http.post<void>(this.authUrl + 'login', {username, password}).pipe(
      tap(() => {
        this.isAuthenticated.set(true);
        this._lastChecked = Date.now();
      }),
    );
  }

  logout(): Observable<void> {
    return this.http.post<void>(this.authUrl + 'logout', {}).pipe(
      tap(() => {
        this.isAuthenticated.set(false);
        this._lastChecked = 0;
      }),
    );
  }

  checkAuthStatus(): Observable<boolean> {
    // Return cached result if authenticated and checked within the last 60 seconds
    if (this.isAuthenticated() && Date.now() - this._lastChecked < this.CACHE_TTL) {
      return of(true);
    }
    return this.http.get<{authenticated: boolean}>(this.authUrl + 'status').pipe(
      map((res) => {
        this.isAuthenticated.set(res.authenticated);
        this._lastChecked = Date.now();
        return res.authenticated;
      }),
      catchError(() => {
        this.isAuthenticated.set(false);
        this._lastChecked = 0;
        return of(false);
      }),
    );
  }
}

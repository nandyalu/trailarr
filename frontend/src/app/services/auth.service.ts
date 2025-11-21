import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  constructor(private http: HttpClient) { }

  login(credentials: any): Observable<any> {
    return this.http.post('/api/v1/token', credentials)
      .pipe(
        tap((response: any) => {
          this.setToken(response.access_token);
        })
      );
  }

  logout(): void {
    this.removeToken();
  }

  private setToken(token: string): void {
    document.cookie = `trailarr_api_key=${token}; SameSite=Strict; Path=/`;
  }

  private removeToken(): void {
    document.cookie = 'trailarr_api_key=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  }
}

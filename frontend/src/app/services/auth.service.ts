import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { environment } from '../../environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private authUrl = environment.apiUrl + environment.login;

  apiKey: string = sessionStorage.getItem('api_key') || '';

  constructor(private http: HttpClient) {  }

  // Check if the API key is stored in the session storage and return it
  // If not, get the API key from the server
  getApiKey(): Observable<string> {
    if (this.apiKey) {
      return of(this.apiKey);
    }
    const storedKey = sessionStorage.getItem('api_key');
    if (storedKey) {
      this.apiKey = storedKey;
      return of(this.apiKey);
    }
    return this.getApiKeyFromServer();
  }

  // Get the API key from the server
  getApiKeyFromServer(): Observable<string> {
    const user = {
      username: environment.username,
      password: environment.password
    };
    // Get API key from the server using the user credentials
    return this.http.post<string>(this.authUrl, user);
  }
}

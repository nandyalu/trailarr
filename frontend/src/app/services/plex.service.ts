import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from 'src/environment';

// Plex API interfaces matching backend models
export interface AuthStartRequest {
  client_identifier: string;
  product_name: string;
}

export interface AuthStartResponse {
  pin: string;
  auth_url: string;
  expires_in: string;
}

export interface AuthPollResponse {
  status: 'pending' | 'success' | 'expired';
  token?: string;
  plex_server_address?: string;
}

export interface ScanRequest {
  token: string;
  server_address: string;
  media_folder_path: string;
}

export interface ScanResponse {
  success: boolean;
  message: string;
}

export interface ExtrasRequest {
  token: string;
  server_address: string;
  media_type: 'movie' | 'show';
  tmdb_id?: string;
  tvdb_id?: string;
}

export interface ExtraDetail {
  title: string;
  type: string;
  duration: number;
}

export interface ExtrasResponse {
  has_extras: boolean;
  extras: ExtraDetail[];
  message: string;
}

@Injectable({
  providedIn: 'root',
})
export class PlexService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl + '/plex';

  /**
   * Start the Plex authentication flow.
   */
  startAuth(request: AuthStartRequest): Observable<AuthStartResponse> {
    return this.http.post<AuthStartResponse>(`${this.baseUrl}/auth/start`, request);
  }

  /**
   * Poll for authentication token using PIN.
   */
  pollForToken(pin: string): Observable<AuthPollResponse> {
    return this.http.get<AuthPollResponse>(`${this.baseUrl}/auth/poll/${pin}`);
  }

  /**
   * Trigger a media library scan on Plex server.
   */
  triggerScan(request: ScanRequest): Observable<ScanResponse> {
    return this.http.post<ScanResponse>(`${this.baseUrl}/scan`, request);
  }

  /**
   * Check for media extras in Plex library.
   */
  checkExtras(request: ExtrasRequest): Observable<ExtrasResponse> {
    return this.http.post<ExtrasResponse>(`${this.baseUrl}/extras`, request);
  }
}
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {inject, Injectable} from '@angular/core';
import {map, Observable} from 'rxjs';
import {SettingsService} from './settings.service';

/** Plex PIN response from https://plex.tv/api/v2/pins */
export interface PlexPin {
  id: number;
  code: string;
  /** ISO-8601 expiry timestamp */
  expiresAt: string;
  /** Populated once the user approves in the Plex UI */
  authToken: string | null;
}

/** A reachable Plex server returned from the resources endpoint */
export interface PlexServer {
  name: string;
  /** All available connection URIs for this server */
  uris: string[];
}

const PLEX_TV_BASE = 'https://plex.tv/api/v2';
const PLEX_CLIENTS_BASE = 'https://clients.plex.tv/api/v2';
const PLEX_DEVICE_NAME = 'Trailarr Plex Connection'; // Shown as device name in Plex UI
// PLEX_VERSION is read dynamically from SettingsService (see appVersion getter)
const PLEX_PRODUCT = 'Trailarr'; // Shown as product in Plex UI and used for client identification
const PLEX_DEVICE = 'Trailarr Server'; // Shown as device in Plex UI

/**
 * Handles Plex OAuth directly from the browser.
 *
 * Flow:
 *   1. requestPin()     → get { id, code } + build auth URL
 *   2. Open auth URL in a new tab
 *   3. Poll pollPin()   → wait for authToken
 *   4. getServers()     → list available Plex Media Servers
 */
@Injectable({providedIn: 'root'})
export class PlexOAuthService {
  private readonly http = inject(HttpClient);
  private readonly settings = inject(SettingsService);

  private get appVersion(): string {
    return this.settings.settingsResource.value()?.version ?? '1.0';
  }

  private plexHeaders(clientId: string): HttpHeaders {
    return new HttpHeaders({
      Accept: 'application/json',
      'X-Plex-Product': PLEX_PRODUCT,
      'X-Plex-Version': this.appVersion,
      'X-Plex-Device': PLEX_DEVICE,
      'X-Plex-Device-Name': PLEX_DEVICE_NAME,
      'X-Plex-Client-Identifier': clientId,
    });
  }

  /**
   * Request a new PIN from plex.tv.
   * The PIN id + code are used to build the auth URL and to poll for the token.
   */
  requestPin(clientId: string): Observable<PlexPin> {
    return this.http.post<PlexPin>(`${PLEX_TV_BASE}/pins?strong=true`, null, {
      headers: this.plexHeaders(clientId),
    });
  }

  /**
   * Build the plex.tv auth URL that the user must open.
   * Include a forwardUrl so Plex redirects back after auth (optional, ignored if blank).
   */
  buildAuthUrl(pinCode: string, clientId: string): string {
    const s = this.settings.settingsResource.value();
    const params = new URLSearchParams({
      clientID: clientId,
      code: pinCode,
      'context[device][product]': PLEX_PRODUCT,
      'context[device][version]': this.appVersion,
      'context[device][device]': PLEX_DEVICE,
      'context[device][deviceName]': PLEX_DEVICE_NAME,
      'context[device][platform]': s?.server_platform ?? 'Linux',
      'context[device][platformVersion]': s?.server_platform_version ?? 'unknown',
      'context[device][model]': s?.server_model ?? 'unknown',
      'context[device][deviceVendor]': s?.server_hostname ?? 'Trailarr',
    });
    return `https://app.plex.tv/auth#?${params.toString()}`;
  }

  /**
   * Poll for the PIN status. Returns the updated PlexPin — check authToken !== null
   * to know if the user has approved.
   */
  pollPin(pinId: number, clientId: string): Observable<PlexPin> {
    return this.http.get<PlexPin>(`${PLEX_TV_BASE}/pins/${pinId}`, {
      headers: this.plexHeaders(clientId),
    });
  }

  /**
   * Fetch all owned Plex Media Servers the token has access to.
   * Returns only servers with at least one local (non-relay) direct connection.
   */
  getServers(token: string, clientId: string): Observable<PlexServer[]> {
    const headers = this.plexHeaders(clientId).set('X-Plex-Token', token);
    const url = `${PLEX_CLIENTS_BASE}/resources?includeHttps=1&includeRelay=1&includeIPv6=1`;
    return this.http.get<any[]>(url, {headers}).pipe(
      map((resources) => {
        const servers: PlexServer[] = [];
        for (const r of resources) {
          if (!r.owned || r.product !== 'Plex Media Server') continue;
          const uris: string[] = (r.connections ?? []).filter((c: any) => c.uri).map((c: any) => c.uri as string);
          if (uris.length > 0) {
            servers.push({name: r.name, uris});
          }
        }
        return servers;
      }),
    );
  }
}

import {HttpClient} from '@angular/common/http';
import {inject, Injectable, signal} from '@angular/core';
import {Observable, tap} from 'rxjs';
import {environment} from '../../environment';
import {SetupStatus} from '../models/setup';

/**
 * The first-run setup guide.
 *
 * The backend decides whether the guide is needed, once, and records it.
 * The frontend never decides from "there are no connections": someone who
 * removes their last connection is not a new user.
 */
@Injectable({providedIn: 'root'})
export class SetupService {
  private readonly httpClient = inject(HttpClient);
  private readonly setupUrl = `${environment.apiUrl}setup/`;

  /** The last status read from the server, for guards and the guide. */
  readonly status = signal<SetupStatus | undefined>(undefined);

  /** Reads whether this installation still needs the guide. */
  loadStatus(): Observable<SetupStatus> {
    return this.httpClient
      .get<SetupStatus>(`${this.setupUrl}status`)
      .pipe(tap((status) => this.status.set(status)));
  }

  /** Records that the guide is behind this installation — finished or skipped. */
  complete(): Observable<SetupStatus> {
    return this.httpClient
      .post<SetupStatus>(`${this.setupUrl}complete`, {})
      .pipe(tap((status) => this.status.set(status)));
  }
}

import {HttpClient, httpResource} from '@angular/common/http';
import {computed, inject, Injectable} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {firstValueFrom} from 'rxjs';
import {environment} from '../../environment';
import {hasUrgentIssues, Issue} from '../models/issue';
import {WebsocketService} from './websocket.service';

@Injectable({
  providedIn: 'root',
})
export class IssueService {
  private readonly httpClient = inject(HttpClient);
  private readonly webSocketService = inject(WebsocketService);

  private readonly issuesUrl = environment.apiUrl + 'issues/';

  readonly issuesResource = httpResource<Issue[]>(() => ({url: this.issuesUrl}), {
    defaultValue: [],
    parse: (response) => (Array.isArray(response) ? (response as Issue[]) : []),
  });

  readonly openCount = computed(() => this.issuesResource.value().length);

  readonly hasUrgent = computed(() => hasUrgentIssues(this.issuesResource.value()));

  constructor() {
    this.webSocketService.toastMessage.pipe(takeUntilDestroyed()).subscribe((msg) => {
      if (msg.reload?.includes('issues')) {
        this.issuesResource.reload();
      }
    });
  }

  async dismissIssue(id: number): Promise<void> {
    await firstValueFrom(this.httpClient.delete(`${this.issuesUrl}${id}`));
    this.issuesResource.reload();
  }
}

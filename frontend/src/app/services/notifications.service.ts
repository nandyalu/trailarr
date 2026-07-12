import {HttpClient, httpResource} from '@angular/common/http';
import {inject, Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {environment} from 'src/environment';
import {NotificationChannelCreate, NotificationChannelRead} from '../models/notificationchannel';

@Injectable({
  providedIn: 'root',
})
export class NotificationsService {
  private readonly http = inject(HttpClient);
  private readonly notificationsUrl = environment.apiUrl + environment.notifications;

  readonly allChannels = httpResource<NotificationChannelRead[]>(() => this.notificationsUrl, {defaultValue: []});

  createChannel(channel: NotificationChannelCreate): Observable<NotificationChannelRead> {
    return this.http.post<NotificationChannelRead>(this.notificationsUrl, channel);
  }

  updateChannel(id: number, channel: NotificationChannelCreate): Observable<NotificationChannelRead> {
    return this.http.put<NotificationChannelRead>(`${this.notificationsUrl}${id}`, channel);
  }

  deleteChannel(id: number): Observable<string> {
    return this.http.delete<string>(`${this.notificationsUrl}${id}`);
  }

  testChannel(id: number): Observable<string> {
    return this.http.post<string>(`${this.notificationsUrl}${id}/test`, {});
  }
}

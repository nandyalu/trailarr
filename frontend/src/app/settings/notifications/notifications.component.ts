import {ChangeDetectionStrategy, Component, computed, inject, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {OptionsSettingComponent} from 'src/app/settings/profiles/settings/options-setting/options-setting.component';
import {EVENT_TYPE_LABELS, EventType} from 'src/app/models/event';
import {NotificationChannelCreate, NotificationChannelRead} from 'src/app/models/notificationchannel';
import {NotificationsService} from 'src/app/services/notifications.service';
import {WebsocketService} from 'src/app/services/websocket.service';

@Component({
  selector: 'app-settings-notifications',
  imports: [FormsModule, OptionsSettingComponent],
  templateUrl: './notifications.component.html',
  styleUrl: './notifications.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotificationsComponent {
  private readonly notificationsService = inject(NotificationsService);
  private readonly webSocketService = inject(WebsocketService);

  protected readonly channels = computed(() => this.notificationsService.allChannels.value());
  protected readonly isLoading = computed(() => this.notificationsService.allChannels.isLoading());

  protected readonly trueFalseOptions = ['true', 'false'];

  // All subscribable event types with display labels
  protected readonly eventTypeOptions = Object.values(EventType).map((value) => ({
    name: this.toEventName(value),
    label: EVENT_TYPE_LABELS[value],
  }));

  // Dialog state
  protected readonly dialogOpen = signal(false);
  protected readonly editingId = signal<number | null>(null);
  protected readonly testingId = signal<number | null>(null);
  protected formName = '';
  protected formUrl = '';
  protected readonly formEnabled = signal(true);
  protected readonly formIncludeUserEvents = signal(false);
  protected formEventTypes = new Set<string>();

  /** EventType enum stores lowercase values; the API subscribes by NAME */
  private toEventName(value: string): string {
    return value.toUpperCase();
  }

  protected setEnabled(option: string): void {
    this.formEnabled.set(option === 'true');
  }

  protected setIncludeUserEvents(option: string): void {
    this.formIncludeUserEvents.set(option === 'true');
  }

  protected reloadChannels(): void {
    this.notificationsService.allChannels.reload();
  }

  protected eventLabelsFor(channel: NotificationChannelRead): string {
    const labels = this.eventTypeOptions.filter((o) => channel.event_types.includes(o.name)).map((o) => o.label);
    return labels.length > 0 ? labels.join(', ') : 'No events selected';
  }

  protected openAddDialog(): void {
    this.editingId.set(null);
    this.formName = '';
    this.formUrl = '';
    this.formEnabled.set(true);
    this.formIncludeUserEvents.set(false);
    this.formEventTypes = new Set(['TRAILER_DOWNLOADED']);
    this.dialogOpen.set(true);
  }

  protected openEditDialog(channel: NotificationChannelRead): void {
    this.editingId.set(channel.id);
    this.formName = channel.name;
    this.formUrl = ''; // write-only: blank = keep existing
    this.formEnabled.set(channel.enabled);
    this.formIncludeUserEvents.set(channel.include_user_events);
    this.formEventTypes = new Set(channel.event_types);
    this.dialogOpen.set(true);
  }

  protected toggleEventType(name: string): void {
    if (this.formEventTypes.has(name)) {
      this.formEventTypes.delete(name);
    } else {
      this.formEventTypes.add(name);
    }
  }

  protected saveChannel(): void {
    const payload: NotificationChannelCreate = {
      name: this.formName.trim(),
      url: this.formUrl.trim(),
      enabled: this.formEnabled(),
      event_types: [...this.formEventTypes],
      include_user_events: this.formIncludeUserEvents(),
    };
    const id = this.editingId();
    const request =
      id === null ? this.notificationsService.createChannel(payload) : this.notificationsService.updateChannel(id, payload);
    request.subscribe({
      next: () => {
        this.dialogOpen.set(false);
        this.notificationsService.allChannels.reload();
        this.webSocketService.showToast(id === null ? 'Notification channel added!' : 'Notification channel updated!');
      },
      error: (error) => {
        this.webSocketService.showToast(error.error?.detail || 'Failed to save channel!', 'Error');
      },
    });
  }

  protected deleteChannel(channel: NotificationChannelRead): void {
    if (!confirm(`Delete notification channel '${channel.name}'?`)) {
      return;
    }
    this.notificationsService.deleteChannel(channel.id).subscribe({
      next: () => {
        this.notificationsService.allChannels.reload();
        this.webSocketService.showToast('Notification channel deleted!');
      },
      error: (error) => {
        this.webSocketService.showToast(error.error?.detail || 'Failed to delete channel!', 'Error');
      },
    });
  }

  protected testChannel(channel: NotificationChannelRead): void {
    this.testingId.set(channel.id);
    this.notificationsService.testChannel(channel.id).subscribe({
      next: (msg) => {
        this.testingId.set(null);
        this.webSocketService.showToast(msg || 'Test notification sent!');
      },
      error: (error) => {
        this.testingId.set(null);
        this.webSocketService.showToast(error.error?.detail || 'Test notification failed!', 'Error');
      },
    });
  }
}

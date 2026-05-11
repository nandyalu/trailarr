import {ChangeDetectionStrategy, Component, inject, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {MessageData, WebsocketService} from '../services/websocket.service';

@Component({
  selector: 'app-notifications',
  templateUrl: './notifications.component.html',
  styleUrl: './notifications.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NotificationsComponent {
  private readonly websocketService = inject(WebsocketService);

  protected readonly messages = signal<MessageData[]>([]);
  protected readonly pinnedToasts = signal(new Set<MessageData>());
  protected readonly hoveredToasts = signal(new Set<MessageData>());
  private readonly toastTimeouts = new Map<MessageData, ReturnType<typeof setTimeout>>();

  constructor() {
    this.websocketService.toastMessage.pipe(takeUntilDestroyed()).subscribe((data) => {
      this.messages.update((msgs) => [...msgs, data]);
      const id = setTimeout(() => this.removeMessage(data), 3000);
      this.toastTimeouts.set(data, id);
    });
  }

  protected removeMessage(data: MessageData): void {
    clearTimeout(this.toastTimeouts.get(data));
    this.toastTimeouts.delete(data);
    this.pinnedToasts.update((s) => { const n = new Set(s); n.delete(data); return n; });
    this.hoveredToasts.update((s) => { const n = new Set(s); n.delete(data); return n; });
    this.messages.update((msgs) => msgs.filter((m) => m !== data));
  }

  protected stopAutoClose(data: MessageData): void {
    clearTimeout(this.toastTimeouts.get(data));
    this.toastTimeouts.delete(data);
    this.pinnedToasts.update((s) => new Set(s).add(data));
  }

  protected pauseAutoClose(data: MessageData): void {
    clearTimeout(this.toastTimeouts.get(data));
    this.toastTimeouts.delete(data);
    this.hoveredToasts.update((s) => new Set(s).add(data));
  }

  protected resumeIfNotPinned(data: MessageData): void {
    this.hoveredToasts.update((s) => { const n = new Set(s); n.delete(data); return n; });
    if (this.pinnedToasts().has(data)) return;
    const id = setTimeout(() => this.removeMessage(data), 3000);
    this.toastTimeouts.set(data, id);
  }

  protected onToastAction(data: MessageData): void {
    if (this.pinnedToasts().has(data)) {
      this.removeMessage(data);
    } else {
      this.stopAutoClose(data);
    }
  }
}

import {AsyncPipe, TitleCasePipe} from '@angular/common';
import {httpResource} from '@angular/common/http';
import {ChangeDetectionStrategy, Component, computed, inject, input} from '@angular/core';
import {TimediffPipe} from 'src/app/helpers/timediff.pipe';
import {EVENT_TYPE_LABELS, EventRead, EventType} from 'src/app/models/event';
import {EventsService} from 'src/app/services/events.service';

@Component({
  selector: 'media-events',
  imports: [TitleCasePipe, TimediffPipe, AsyncPipe],
  templateUrl: './media-events.component.html',
  styleUrl: './media-events.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MediaEventsComponent {
  private readonly eventsService = inject(EventsService);

  mediaId = input.required<number>();

  protected readonly eventTypeLabels = EVENT_TYPE_LABELS;
  protected readonly eventTypes = EventType;

  protected readonly events = httpResource<EventRead[]>(
    () => ({
      url: `${this.eventsService.eventsUrl}media/${this.mediaId()}`,
      method: 'GET',
    }),
    {defaultValue: []},
  );

  protected readonly isLoading = computed(() => this.events.isLoading());

  protected readonly eventsList = computed(() => this.events.value());

  protected readonly hasEvents = computed(() => this.eventsList().length > 0);

  getEventDescription(event: EventRead): string {
    switch (event.event_type) {
      case EventType.MEDIA_ADDED:
        return 'Media was added to the library';
      case EventType.MONITOR_CHANGED:
        if (event.old_value === 'true' && event.new_value === 'false') {
          return 'Monitoring disabled';
        } else if (event.old_value === 'false' && event.new_value === 'true') {
          return 'Monitoring enabled';
        }
        return `Monitor: ${event.old_value} → ${event.new_value}`;
      case EventType.YOUTUBE_ID_CHANGED:
        if (!event.old_value && event.new_value) {
          return `YouTube ID set to ${event.new_value}`;
        } else if (event.old_value && !event.new_value) {
          return `YouTube ID cleared (was ${event.old_value})`;
        }
        return `YouTube ID: ${event.old_value || 'none'} → ${event.new_value || 'none'}`;
      case EventType.TRAILER_DETECTED:
        return event.new_value ? `Trailer detected: ${event.new_value}` : 'Existing trailer detected';
      case EventType.TRAILER_DOWNLOADED:
        return event.new_value ? `Downloaded from ${event.new_value}` : 'Trailer downloaded';
      case EventType.TRAILER_DELETED:
        return event.new_value ? `Deleted: ${event.new_value}` : 'Trailer deleted';
      case EventType.DOWNLOAD_SKIPPED:
        return event.new_value || 'Download was skipped';
      case EventType.PLEX_LINKED:
        return `Linked to Plex: ${event.new_value}`;
      case EventType.PLEX_UNLINKED:
        return `Unlinked from Plex: ${event.old_value}`;
      case EventType.PLEX_SCAN_TRIGGERED:
        return event.new_value ? `Scan path: ${event.new_value}` : 'Plex scan triggered';
      default:
        return '';
    }
  }
}

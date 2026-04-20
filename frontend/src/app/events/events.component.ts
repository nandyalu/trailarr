import {AsyncPipe, TitleCasePipe} from '@angular/common';
import {httpResource} from '@angular/common/http';
import {ChangeDetectionStrategy, Component, computed, DestroyRef, effect, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {ActivatedRoute, RouterLink} from '@angular/router';
import {debounceTime, distinctUntilChanged} from 'rxjs';
import {ScrollNearEndDirective} from '../helpers/scroll-near-end-directive';
import {TimediffPipe} from '../helpers/timediff.pipe';
import {EVENT_SOURCE_LABELS, EVENT_TYPE_LABELS, EventRead, EventSource, EventType} from '../models/event';
import {EventsService} from '../services/events.service';
import {MediaService} from '../services/media.service';
import {LoadIndicatorComponent} from '../shared/load-indicator';

@Component({
  selector: 'app-events',
  imports: [
    AsyncPipe,
    FormsModule,
    LoadIndicatorComponent,
    ReactiveFormsModule,
    RouterLink,
    ScrollNearEndDirective,
    TimediffPipe,
    TitleCasePipe,
  ],
  templateUrl: './events.component.html',
  styleUrl: './events.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EventsComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  private readonly eventsService = inject(EventsService);
  private readonly mediaService = inject(MediaService);
  private readonly route = inject(ActivatedRoute);

  readonly title = 'Events';
  readonly eventTypes = EventType;
  readonly eventSources = EventSource;
  readonly allEventTypes = Object.values(EventType);
  readonly allEventSources = Object.values(EventSource);
  readonly eventTypeLabels = EVENT_TYPE_LABELS;
  readonly eventSourceLabels = EVENT_SOURCE_LABELS;

  searchForm = new FormControl();
  displayCount = signal(50);

  protected readonly allEvents = httpResource<EventRead[]>(
    () => ({
      url: this.eventsService.eventsUrl,
      method: 'GET',
      params: {
        limit: this.limit(),
        ...(this.selectedEventType() !== 'all' ? {event_type: this.selectedEventType()} : {}),
        ...(this.selectedEventSource() !== 'all' ? {event_source: this.selectedEventSource()} : {}),
      },
    }),
    {defaultValue: []},
  );

  searchQuery = signal<string>('');
  selectedEventType = signal<EventType | 'all'>('all');
  selectedEventSource = signal<EventSource | 'all'>('all');
  limit = signal(500);

  // Map of media ID to media title for display
  protected readonly mediaTitlesMap = computed(() => {
    const media = this.mediaService.combinedMedia();
    const titlesMap = new Map<number, string>();
    media.forEach((m) => titlesMap.set(m.id, m.title));
    return titlesMap;
  });

  getMediaTitle(mediaId: number): string {
    return this.mediaTitlesMap().get(mediaId) || `Media #${mediaId}`;
  }

  filteredEvents = computed(() => {
    const query = this.searchQuery().toLowerCase();
    let events = this.allEvents.value();

    if (query && query.trim().length > 0) {
      const titlesMap = this.mediaTitlesMap();
      events = events.filter(
        (event) =>
          (event.source_detail || '').toLowerCase().includes(query) ||
          (event.old_value || '').toLowerCase().includes(query) ||
          (event.new_value || '').toLowerCase().includes(query) ||
          event.event_type.toLowerCase().replaceAll('_', ' ').includes(query) ||
          (titlesMap.get(event.media_id) || '').toLowerCase().includes(query),
      );
    }

    return events.slice(0, this.displayCount());
  });

  resetDisplayCount = effect(() => {
    this.searchQuery();
    this.selectedEventType();
    this.selectedEventSource();
    this.displayCount.set(50);
  });

  ngOnInit() {
    this.route.queryParams.subscribe((params) => {
      const eventType = params['type'];
      if (eventType && Object.values(EventType).includes(eventType)) {
        this.selectedEventType.set(eventType);
      }
      const mediaId = params['media_id'];
      if (mediaId) {
        this.searchForm.setValue(mediaId);
        this.searchQuery.set(mediaId);
      }
    });

    this.searchForm.valueChanges.pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef)).subscribe((value) => {
      this.searchQuery.set(value || '');
    });
  }

  getEventIcon(eventType: EventType): string {
    switch (eventType) {
      case EventType.MEDIA_ADDED:
        return 'add_circle';
      case EventType.MONITOR_CHANGED:
        return 'visibility';
      case EventType.YOUTUBE_ID_CHANGED:
        return 'link';
      case EventType.TRAILER_DETECTED:
        return 'search';
      case EventType.TRAILER_DOWNLOADED:
        return 'download';
      case EventType.TRAILER_DELETED:
        return 'delete';
      case EventType.DOWNLOAD_SKIPPED:
        return 'block';
      case EventType.PLEX_LINKED:
        return 'link';
      case EventType.PLEX_UNLINKED:
        return 'link_off';
      case EventType.PLEX_SCAN_TRIGGERED:
        return 'sync';
      default:
        return 'info';
    }
  }

  getEventDescription(event: EventRead): string {
    switch (event.event_type) {
      case EventType.MEDIA_ADDED:
        return `Added from ${event.new_value}`;
      case EventType.MONITOR_CHANGED:
        return `Monitor: ${event.old_value} → ${event.new_value}`;
      case EventType.YOUTUBE_ID_CHANGED:
        const oldId = event.old_value || '(none)';
        const newId = event.new_value || '(none)';
        return `YouTube ID: ${oldId} → ${newId}`;
      case EventType.TRAILER_DETECTED:
        return 'Existing trailer detected on disk';
      case EventType.TRAILER_DOWNLOADED:
        return `Downloaded trailer: ${event.new_value}`;
      case EventType.TRAILER_DELETED:
        return `Trailer deleted: ${event.new_value || 'unknown reason'}`;
      case EventType.DOWNLOAD_SKIPPED:
        return `Skipped: ${event.new_value}`;
      case EventType.PLEX_LINKED:
        return `Linked to Plex connection: ${event.new_value}`;
      case EventType.PLEX_UNLINKED:
        return `Unlinked from Plex connection: ${event.old_value}`;
      case EventType.PLEX_SCAN_TRIGGERED:
        return `Plex scan triggered for: ${event.new_value}`;
      default:
        return event.new_value || event.old_value || '';
    }
  }

  loadMore() {
    const currentCount = this.displayCount();
    const events = this.allEvents.value();

    if (currentCount >= events.length) {
      if (events.length >= this.limit()) {
        this.limit.update((limit) => limit + 500);
      }
      return;
    }
    this.displayCount.set(currentCount + 30);
  }
}

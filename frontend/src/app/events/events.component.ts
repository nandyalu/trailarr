import {AsyncPipe, TitleCasePipe} from '@angular/common';
import {httpResource} from '@angular/common/http';
import {ChangeDetectionStrategy, Component, computed, DestroyRef, effect, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormControl, ReactiveFormsModule} from '@angular/forms';
import {ActivatedRoute, Router, RouterLink} from '@angular/router';
import {debounceTime, distinctUntilChanged, take} from 'rxjs';
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
  private readonly router = inject(Router);

  readonly title = 'Events';
  readonly eventTypes = EventType;
  readonly eventSources = EventSource;
  readonly allEventTypes = Object.values(EventType);
  readonly allEventSources = Object.values(EventSource);
  readonly eventTypeLabels = EVENT_TYPE_LABELS;
  readonly eventSourceLabels = EVENT_SOURCE_LABELS;

  searchForm = new FormControl();
  displayCount = signal(50);
  searchQuery = signal<string>('');
  selectedEventType = signal<EventType | 'all'>('all');
  selectedEventSource = signal<EventSource | 'all'>('all');
  limit = signal(500);

  readonly selectedSourceLabel = computed(() => {
    const src = this.selectedEventSource();
    return src === 'all' ? 'All Sources' : this.eventSourceLabels[src];
  });

  readonly selectedTypeLabel = computed(() => {
    const type = this.selectedEventType();
    return type === 'all' ? 'All Events' : this.eventTypeLabels[type];
  });

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

  setEventType(type: EventType | 'all'): void {
    this.selectedEventType.set(type);
    this.persistState();
  }

  setEventSource(source: EventSource | 'all'): void {
    this.selectedEventSource.set(source);
    this.persistState();
  }

  private persistState(): void {
    const type = this.selectedEventType();
    const source = this.selectedEventSource();
    const q = this.searchQuery();

    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        type: type !== 'all' ? type : null,
        source: source !== 'all' ? source : null,
        q: q || null,
      },
      replaceUrl: true,
    });

    if (type !== 'all') localStorage.setItem('TrailarrEventsType', type);
    else localStorage.removeItem('TrailarrEventsType');

    if (source !== 'all') localStorage.setItem('TrailarrEventsSource', source);
    else localStorage.removeItem('TrailarrEventsSource');

    if (q) localStorage.setItem('TrailarrEventsSearch', q);
    else localStorage.removeItem('TrailarrEventsSearch');
  }

  ngOnInit() {
    // Read localStorage first (lower priority)
    const savedType = localStorage.getItem('TrailarrEventsType') as EventType;
    if (savedType && Object.values(EventType).includes(savedType)) {
      this.selectedEventType.set(savedType);
    }
    const savedSource = localStorage.getItem('TrailarrEventsSource') as EventSource;
    if (savedSource && Object.values(EventSource).includes(savedSource)) {
      this.selectedEventSource.set(savedSource);
    }
    const savedSearch = localStorage.getItem('TrailarrEventsSearch');
    if (savedSearch) {
      this.searchForm.setValue(savedSearch);
      this.searchQuery.set(savedSearch);
    }

    // Read URL params — overrides localStorage (take(1): only initial params, we own the URL after that)
    this.route.queryParams.pipe(take(1)).subscribe((params) => {
      const type = params['type'];
      if (type && Object.values(EventType).includes(type)) {
        this.selectedEventType.set(type as EventType);
      }
      const source = params['source'];
      if (source && Object.values(EventSource).includes(source)) {
        this.selectedEventSource.set(source as EventSource);
      }
      const q = params['q'];
      if (q) {
        this.searchForm.setValue(q);
        this.searchQuery.set(q);
      }
      // media_id is a one-shot deep link from the media detail page
      const mediaId = params['media_id'];
      if (mediaId) {
        this.searchForm.setValue(mediaId);
        this.searchQuery.set(mediaId);
      }
    });

    this.searchForm.valueChanges.pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef)).subscribe((value) => {
      this.searchQuery.set(value || '');
      this.persistState();
    });
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

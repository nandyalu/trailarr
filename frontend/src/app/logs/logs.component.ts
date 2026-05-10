import {AsyncPipe, TitleCasePipe} from '@angular/common';
import {httpResource} from '@angular/common/http';
import {ChangeDetectionStrategy, Component, computed, DestroyRef, effect, ElementRef, inject, OnInit, signal, viewChild} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormControl, ReactiveFormsModule} from '@angular/forms';
import {ActivatedRoute, Router, RouterLink} from '@angular/router';
import {AppLogRecord, LogLevel} from '../models/logs';
import {debounceTime, distinctUntilChanged, take} from 'rxjs';
import {ScrollNearEndDirective} from '../helpers/scroll-near-end-directive';
import {TimediffPipe} from '../helpers/timediff.pipe';
import {LogsService} from '../services/logs.service';
import {LoadIndicatorComponent} from '../shared/load-indicator';

@Component({
  selector: 'app-logs',
  imports: [
    AsyncPipe,
    LoadIndicatorComponent,
    ReactiveFormsModule,
    RouterLink,
    ScrollNearEndDirective,
    TimediffPipe,
    TitleCasePipe,
  ],
  templateUrl: './logs.component.html',
  styleUrl: './logs.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LogsComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  private readonly logsService = inject(LogsService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly title = 'Logs';
  readonly logLevels = LogLevel;
  readonly allLogLevels = Object.values(LogLevel);

  searchForm = new FormControl();
  displayCount = signal(100);

  tracebackLog = signal<AppLogRecord | null>(null);
  private readonly tracebackDialog = viewChild<ElementRef<HTMLDialogElement>>('tracebackDialog');

  protected readonly allLogs = httpResource<AppLogRecord[]>(
    () => ({
      url: this.logsService.logsUrl + 'raw',
      method: 'GET',
      params: {level: this.selectedLogLevel().toUpperCase(), limit: this.limit()},
    }),
    {defaultValue: []},
  );

  protected readonly searchFilterLogs = httpResource<AppLogRecord[]>(
    () => {
      const query = this.searchQuery();
      if (!query || query.length < 3) return undefined;
      return {
        url: this.logsService.logsUrl + 'raw',
        method: 'GET',
        params: {filter: query, level: this.selectedLogLevel().toUpperCase(), limit: this.limit()},
      };
    },
    {defaultValue: []},
  );

  searchQuery = signal<string>('');
  selectedLogLevel = signal(LogLevel.Info);
  limit = signal(1000);

  filteredLogs = computed(() => {
    const query = this.searchQuery();
    const logs = this.allLogs.value();
    const searchLogs = this.searchFilterLogs.value();
    if (query && query.trim().length > 0) {
      return searchLogs.slice(0, this.displayCount());
    }
    return logs.slice(0, this.displayCount());
  });

  resetDisplayCount = effect(() => {
    if (this.searchQuery().length < 3) {
      this.displayCount.set(100);
    }
    this.selectedLogLevel();
    this.displayCount.set(100);
  });

  setLogLevel(level: LogLevel): void {
    this.selectedLogLevel.set(level);
    this.persistState();
  }

  private persistState(): void {
    const level = this.selectedLogLevel();
    const q = this.searchQuery();

    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        level: level !== LogLevel.Info ? level : null,
        filter: q || null,
      },
      replaceUrl: true,
    });

    if (level !== LogLevel.Info) localStorage.setItem('TrailarrLogsLevel', level);
    else localStorage.removeItem('TrailarrLogsLevel');

    if (q) localStorage.setItem('TrailarrLogsSearch', q);
    else localStorage.removeItem('TrailarrLogsSearch');
  }

  ngOnInit() {
    // Read localStorage first (lower priority)
    const savedLevel = localStorage.getItem('TrailarrLogsLevel') as LogLevel;
    if (savedLevel && Object.values(LogLevel).includes(savedLevel)) {
      this.selectedLogLevel.set(savedLevel);
    }
    const savedSearch = localStorage.getItem('TrailarrLogsSearch');
    if (savedSearch) {
      this.searchForm.setValue(savedSearch);
      this.searchQuery.set(savedSearch);
    }

    // Read URL params — overrides localStorage
    this.route.queryParams.pipe(take(1)).subscribe((params) => {
      const level = params['level'] as LogLevel;
      if (level && Object.values(LogLevel).includes(level)) {
        this.selectedLogLevel.set(level);
      }
      const filter = params['filter'];
      if (filter) {
        this.searchForm.setValue(filter);
        this.searchQuery.set(filter);
      }
    });

    this.searchForm.valueChanges.pipe(debounceTime(400), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef)).subscribe((value) => {
      this.searchQuery.set(value);
      this.persistState();
    });
  }

  getRawLog(log: AppLogRecord): string {
    return `${log.created!}: [${log.level}|${log.filename}|${log.lineno}] ${log.loggername!} ${log.message}`;
  }

  getRawLogWithTraceback(log: AppLogRecord): string {
    let rawlog = this.getRawLog(log);
    if (log.traceback) {
      rawlog += `\nException details:\n${log.traceback}`;
    }
    return rawlog;
  }

  getMediaId(log: AppLogRecord): number | null {
    if (log.mediaid) return log.mediaid;
    const mediaIdMatch = log.message?.match(/\[(\d+)\]/);
    return mediaIdMatch ? parseInt(mediaIdMatch[1], 10) : null;
  }

  openTraceback(log: AppLogRecord) {
    this.tracebackLog.set(log);
    this.tracebackDialog()?.nativeElement.showModal();
  }

  closeTraceback() {
    this.tracebackDialog()?.nativeElement.close();
    this.tracebackLog.set(null);
  }

  onDialogClick(event: MouseEvent) {
    const dialog = this.tracebackDialog()?.nativeElement;
    if (event.target === dialog) this.closeTraceback();
  }

  sortLogsByDateAsc(a: AppLogRecord, b: AppLogRecord): number {
    return new Date(a.created!).getTime() - new Date(b.created!).getTime();
  }

  downloadLogs() {
    const query = this.searchQuery();
    const isSearching = query && query.length >= 3;
    const logs = isSearching ? this.searchFilterLogs.value() : this.allLogs.value();
    const formattedlogs = logs
      .sort(this.sortLogsByDateAsc)
      .map((log) => this.getRawLogWithTraceback(log))
      .join('\n');
    const blob = new Blob([formattedlogs], {type: 'text/plain'});
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trailarr-logs-${new Date().toISOString()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }

  loadMore() {
    const currentCount = this.displayCount();
    const query = this.searchQuery();
    const isSearching = query && query.length >= 3;
    const logs = isSearching ? this.searchFilterLogs.value() : this.allLogs.value();

    if (currentCount >= logs.length) {
      if (logs.length >= this.limit()) {
        this.limit.update((limit) => limit + 1000);
      }
      return;
    }
    this.displayCount.set(currentCount + 30);
  }
}

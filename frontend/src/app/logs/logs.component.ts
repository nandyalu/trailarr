import {AsyncPipe, TitleCasePipe} from '@angular/common';
import {httpResource} from '@angular/common/http';
import {ChangeDetectionStrategy, Component, computed, DestroyRef, effect, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {ActivatedRoute, RouterLink} from '@angular/router';
import {AppLogRecordRead, LogLevel} from 'generated-sources/openapi';
import {debounceTime, distinctUntilChanged} from 'rxjs';
import {ScrollNearEndDirective} from '../helpers/scroll-near-end-directive';
import {TimediffPipe} from '../helpers/timediff.pipe';
import {LogsService} from '../services/logs.service';
import {LoadIndicatorComponent} from '../shared/load-indicator';

@Component({
  selector: 'app-logs',
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
  templateUrl: './logs.component.html',
  styleUrl: './logs.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LogsComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  private readonly logsService = inject(LogsService);
  private readonly route = inject(ActivatedRoute);

  // Component constants
  readonly title = 'Logs';
  readonly logLevels = LogLevel;
  readonly allLogLevels = Object.values(LogLevel);

  // Component properties
  searchForm = new FormControl();
  displayCount = signal(100); // Default display count for logs

  // Component resources
  protected readonly allLogs = httpResource<AppLogRecordRead[]>(
    () => ({
      url: this.logsService.logsUrl + 'raw',
      method: 'GET',
      params: {level: this.selectedLogLevel().toUpperCase(), limit: this.limit()},
    }),
    {
      defaultValue: [],
    },
  );

  protected readonly searchFilterLogs = httpResource<AppLogRecordRead[]>(
    () => {
      const query = this.searchQuery();
      if (!query || query.length < 3) {
        return undefined; // No search if query is empty or too short
      }
      return {
        url: this.logsService.logsUrl + 'raw',
        method: 'GET',
        params: {filter: query, level: this.selectedLogLevel().toUpperCase(), limit: this.limit()},
      };
    },
    {
      defaultValue: [],
    },
  );

  // Component signals
  searchQuery = signal<string>('');
  selectedLogLevel = signal(LogLevel.Info);
  limit = signal(1000); // Default limit for logs
  filteredLogs = computed(() => {
    const query = this.searchQuery();
    const logs = this.allLogs.value();
    const searchLogs = this.searchFilterLogs.value();
    if (query && query.trim().length > 0) {
      return searchLogs.slice(0, this.displayCount()); // Return filtered logs from search API
    }
    return logs.slice(0, this.displayCount()); // Return all logs if no query or too short
  });

  // Component effects
  resetDisplayCount = effect(() => {
    // Reset display count when search query is cleared or too short
    if (this.searchQuery().length < 3) {
      this.displayCount.set(100);
    }
    this.selectedLogLevel();
    this.displayCount.set(100); // Reset display count when log level is changed
  });

  ngOnInit() {
    this.route.queryParams.subscribe((params) => {
      const keyValue = params['filter'];
      if (keyValue) {
        this.searchForm.setValue(keyValue);
        this.searchQuery.set(keyValue);
      }
    });
    this.searchForm.valueChanges.pipe(debounceTime(400), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef)).subscribe((value) => {
      this.searchQuery.set(value);
    });
  }

  getRawLog(log: AppLogRecordRead): string {
    return `${log.created!}: [${log.level}|${log.filename}|${log.lineno}] ${log.loggername!} ${log.message}`;
  }

  getRawLogWithTraceback(log: AppLogRecordRead): string {
    let rawlog = this.getRawLog(log);
    if (log.traceback) {
      rawlog += `\nException details:\n${log.traceback}`;
    }
    return rawlog;
  }

  getMediaId(log: AppLogRecordRead): number | null {
    if (log.mediaid) {
      return log.mediaid;
    }
    // Extract media ID from log message if present (look for " [<digits>] ")
    const mediaIdMatch = log.message?.match(/\[(\d+)\]/);
    return mediaIdMatch ? parseInt(mediaIdMatch[1], 10) : null;
  }

  sortLogsByDateAsc(a: AppLogRecordRead, b: AppLogRecordRead): number {
    return new Date(a.created!).getTime() - new Date(b.created!).getTime();
  }

  // Download logs as a file - All Filtered Logs
  downloadLogs() {
    // Write the logs to a file and download it
    const logs = this.filteredLogs()
      .sort(this.sortLogsByDateAsc)
      .map((log) => this.getRawLogWithTraceback(log))
      .join('\n');
    const blob = new Blob([logs], {type: 'text/plain'});
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
    if (currentCount >= this.allLogs.value().length) {
      this.limit.update((limit) => limit + 1000); // Increase the limit by 1000
      return; // No more logs to load
    }
    // Increase the display count by 30
    this.displayCount.set(currentCount + 30);
  }
}

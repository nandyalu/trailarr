import {TitleCasePipe} from '@angular/common';
import {httpResource} from '@angular/common/http';
import {ChangeDetectionStrategy, Component, computed, DestroyRef, effect, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {AppLogRecord, LogLevel} from 'generated-sources/openapi';
import {TimeagoModule} from 'ngx-timeago';
import {debounceTime, distinctUntilChanged} from 'rxjs';
import {ScrollNearEndDirective} from '../helpers/scroll-near-end-directive';
import {LogsService} from '../services/logs.service';
import {LoadIndicatorComponent} from '../shared/load-indicator';

@Component({
  selector: 'app-logs',
  imports: [FormsModule, LoadIndicatorComponent, ReactiveFormsModule, ScrollNearEndDirective, TimeagoModule, TitleCasePipe],
  templateUrl: './logs.component.html',
  styleUrl: './logs.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LogsComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  private readonly logsService = inject(LogsService);

  // Component constants
  readonly title = 'Logs';
  readonly logLevels = LogLevel;
  readonly allLogLevels = Object.values(LogLevel);

  // Component properties
  searchForm = new FormControl();
  displayCount = signal(100); // Default display count for logs

  // Component resources
  protected readonly allLogs = httpResource<AppLogRecord[]>(
    () => ({
      url: this.logsService.logsUrl + 'raw',
      method: 'GET',
      params: {level: this.selectedLogLevel().toUpperCase(), limit: this.limit()},
    }),
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
    if (!query || query.length < 3) {
      return logs.slice(0, this.displayCount()); // Return all logs if no query or too short
    }
    // Filter logs based on the search query
    return logs.filter((log: AppLogRecord) => {
      const objectValues = Object.values(log).map((value) => value?.toString() || '');
      const raw_log = objectValues.join(' | ');
      return raw_log.toLowerCase().includes(query.toLowerCase());
    });
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
    this.searchForm.valueChanges.pipe(debounceTime(400), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef)).subscribe((value) => {
      this.searchQuery.set(value);
    });
  }

  getRawLog(log: AppLogRecord): string {
    return `${log.created!}: [${log.level}|${log.filename}|${log.lineno}] ${log.loggername!} ${log.message}`;
  }

  // Download logs as a file - All Filtered Logs
  downloadLogs() {
    // Write the logs to a file and download it
    const logs = this.filteredLogs()
      .map((log) => this.getRawLog(log))
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

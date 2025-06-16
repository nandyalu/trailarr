
import {Component, DestroyRef, inject, OnInit} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormControl, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {TimeagoModule} from 'ngx-timeago';
import {debounceTime, distinctUntilChanged} from 'rxjs';
import {Logs} from '../models/logs';
import {LogsService} from '../services/logs.service';
import {LoadIndicatorComponent} from '../shared/load-indicator';

@Component({
  selector: 'app-logs',
  imports: [FormsModule, LoadIndicatorComponent, ReactiveFormsModule, TimeagoModule],
  templateUrl: './logs.component.html',
  styleUrl: './logs.component.scss',
})
export class LogsComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  private readonly logsService = inject(LogsService);

  title = 'Logs';
  isLoading = true;
  isUpdating = false;
  all_logs: Logs[] = [];
  searchQuery = '';
  searchForm = new FormControl();
  filtered_logs: Logs[] = [];

  ngOnInit() {
    this.searchForm.valueChanges.pipe(debounceTime(400), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef)).subscribe((value) => {
      this.onSearch(value);
    });

    this.isLoading = true;
    this.getLogs();
  }

  getLogs(): void {
    this.isUpdating = true;
    this.logsService.getLogs().subscribe((logs: Logs[]) => {
      this.all_logs = logs;
      this.filtered_logs = logs;
      this.isLoading = false;
      this.isUpdating = false;
    });
  }

  // downloadLogs(): void {
  //   // this.isUpdating = true;
  //   this.logsService.downloadLogs().subscribe((data: Blob) => {
  //     const url = window.URL.createObjectURL(data);
  //     const a = document.createElement('a');
  //     a.href = url;
  //     a.click();
  //     window.URL.revokeObjectURL(url);
  //     // this.isUpdating = false;
  //     // return data;
  //   });
  // }

  onSearch(query: string = '') {
    if (query.length < 3) {
      this.filtered_logs = this.all_logs;
      return;
    }
    if (query.trim() === this.searchQuery) {
      return;
    }
    this.searchQuery = query;
    // console.log('Search query: %s', this.searchQuery);
    this.filtered_logs = this.all_logs.filter((log: Logs) => {
      return log.raw_log.toLowerCase().includes(this.searchQuery.toLowerCase());
    });
  }
}

import { NgFor, NgIf } from '@angular/common';
import { Component } from '@angular/core';
import { FormControl, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { TimeagoModule } from 'ngx-timeago';
import { debounceTime, distinctUntilChanged } from 'rxjs';
import { Logs } from '../models/logs';
import { LogsService } from '../services/logs.service';

@Component({
    selector: 'app-logs',
    imports: [NgIf, NgFor, FormsModule, ReactiveFormsModule, TimeagoModule],
    templateUrl: './logs.component.html',
    styleUrl: './logs.component.css'
})
export class LogsComponent {

  title = 'Logs';
  isLoading = true;
  isUpdating = false;
  all_logs: Logs[] = [];
  searchQuery = '';
  searchForm = new FormControl();
  filtered_logs: Logs[] = [];

  constructor(private logsService: LogsService) {
    this.searchForm.valueChanges
      .pipe(
        debounceTime(400),
        distinctUntilChanged()
      )
      .subscribe((value) => {
        this.onSearch(value);
      });
  }

  ngOnInit(): void {
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

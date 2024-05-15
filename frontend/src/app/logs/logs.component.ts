import { NgFor, NgIf } from '@angular/common';
import { Component } from '@angular/core';
import { LogsService } from '../services/logs.service';

@Component({
  selector: 'app-logs',
  standalone: true,
  imports: [NgIf, NgFor],
  templateUrl: './logs.component.html',
  styleUrl: './logs.component.css'
})
export class LogsComponent {

  title = 'Logs';
  isLoading = true;
  all_logs: string[] = [];

  constructor(private logsService: LogsService) { }

  ngOnInit(): void {
    this.isLoading = true;
    this.logsService.getLogs().subscribe((logs: string[]) => {
      this.all_logs = logs;
      this.isLoading = false;
    });
  }

}

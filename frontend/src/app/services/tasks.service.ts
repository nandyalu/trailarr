import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../environment';
import { QueuedTask, ScheduledTask } from '../models/tasks';

@Injectable({
  providedIn: 'root'
})
export class TasksService {

  private tasksUrl = environment.apiUrl + environment.tasks;

  constructor(private http: HttpClient) { }

  convertTime(seconds: number): string {
    const timeUnits = [
      { unit: 'second', value: 60 },
      { unit: 'minute', value: 60 },
      { unit: 'hour', value: 24 },
      { unit: 'day', value: 7 },
    ];

    for (const { unit, value } of timeUnits) {
      if (seconds < value) {
        return `${seconds} ${unit}${seconds === 1 ? '' : 's'}`;
      }
      seconds = Math.floor(seconds / value);
    }
    return `${seconds} ${seconds === 1 ? 'week' : 'weeks'}`;
  }

  convertDate(date: string): Date | null {
    return date ? new Date(date + 'Z') : null;
  }

  // formatDuration(duration: string): string {
  //   // Check if the duration contains milliseconds
  //   if (!duration) {
  //     return '0:00:00';
  //   }
  //   if (duration.includes('.')) {
  //     // Remove the milliseconds
  //     duration = duration.split('.')[0];
  //   }
  //   return duration
  // }

  formatDuration(duration: number): string {
    // Convert duration in seconds to HH:MM:SS format
    if (duration < 1) {
      return '00:00:00';
    }
    let hours = Math.floor(duration / 3600).toString().padStart(2, '0');
    let minutes = Math.floor((duration % 3600) / 60).toString().padStart(2, '0');
    let seconds = (duration % 60).toString().padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  }

  private schedulesUrl = this.tasksUrl + 'schedules';
  getScheduledTasks(): Observable<ScheduledTask[]> {
    return this.http.get<{ [key: string]: any }>(this.schedulesUrl).pipe(
      map((all_schedules: { [key: string]: any }) => {
        return Object.entries(all_schedules).map(([id, schedule]) => ({
          id,
          ...schedule,
          interval: this.convertTime(schedule.interval),
          last_run_duration: this.formatDuration(schedule.last_run_duration),
          last_run_start: this.convertDate(schedule.last_run_start),
          next_run: this.convertDate(schedule.next_run)
        }));
      })
    );
  }

  private queueUrl = this.tasksUrl + 'queue';
  getQueuedTasks(): Observable<QueuedTask[]> {
    return this.http.get<{ [key: string]: any }>(this.queueUrl).pipe(
      map((all_queues: { [key: string]: any }) => {
        return Object.entries(all_queues).map(([id, queue]) => ({
          id,
          ...queue,
          duration: this.formatDuration(queue.duration),
          finished: this.convertDate(queue.finished),
          started: this.convertDate(queue.started),
          // end: this.convertDate(queue.end)
        }));
      })
    );
  }

  runScheduledTask(id: string): Observable<any> {
    return this.http.get(this.tasksUrl + 'run/' + id);
  }
  
}

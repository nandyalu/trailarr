import {HttpClient, httpResource} from '@angular/common/http';
import {computed, inject, Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {environment} from '../../environment';
import {QueuedTask, ScheduledTask, TaskConfig, TaskConfigUpdate, TasksData} from '../models/tasks';

@Injectable({
  providedIn: 'root',
})
export class TasksService {
  private readonly http = inject(HttpClient);

  private taskDataUrl = environment.apiUrl + environment.tasksData;
  private tasksUrl = environment.apiUrl + environment.tasks;
  private jobsUrl = environment.apiUrl + environment.jobs;
  private configsUrl = environment.apiUrl + environment.taskConfigs;

  // Resource Signals
  private readonly tasksDataResource = httpResource<TasksData>(() => this.taskDataUrl, {
    defaultValue: {
      tasks: [],
      jobs: [],
      configs: [],
    },
  });

  // Computed Signals
  readonly scheduledTasks = computed<ScheduledTask[]>(() => {
    const tasksData = this.tasksDataResource.value();
    const tasks = tasksData.tasks;
    const jobs = tasksData.jobs;
    const configs = tasksData.configs;
    const configByName = new Map(configs.map((c) => [c.task_name, c]));

    return tasks.map((task) => {
      const latestJob = jobs
        .filter((j) => j.task_id === task.id)
        .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())[0];

      let last_run_start: Date | null = null;
      let last_run_status = 'not run';
      let last_run_duration = '';

      if (latestJob) {
        last_run_start = this.parseDate(latestJob.started_at);
        last_run_status = latestJob.status;
        if (latestJob.ended_at) {
          const durationSeconds = Math.floor((new Date(latestJob.ended_at).getTime() - new Date(latestJob.started_at).getTime()) / 1000);
          last_run_duration = this.formatDuration(durationSeconds);
        } else if (latestJob.status === 'running') {
          last_run_duration = '...';
        }
      }

      const config = configByName.get(task.task_name);

      return {
        id: task.id,
        name: task.task_name,
        task_id: task.task_name,
        task_key: config?.task_key ?? '',
        task_status: task.status,
        interval: task.run_once ? 'once' : this.convertTime(task.interval_seconds),
        interval_seconds: config?.interval_seconds ?? task.interval_seconds,
        delay_seconds: config?.delay_seconds ?? 0,
        last_run_duration,
        last_run_start,
        last_run_status,
        next_run: this.parseDate(task.next_run_at),
      } as ScheduledTask;
    });
  });
  readonly queuedTasks = computed<QueuedTask[]>(() => {
    const tasksData = this.tasksDataResource.value();
    const tasks = tasksData.tasks;
    const jobs = tasksData.jobs;
    const taskNameById = new Map(tasks.map((t) => [t.id, t.task_name]));

    return jobs.map((job) => {
      const taskName = taskNameById.get(job.task_id) ?? job.task_id;

      let duration = '';
      if (job.ended_at) {
        const durationSeconds = Math.floor((new Date(job.ended_at).getTime() - new Date(job.started_at).getTime()) / 1000);
        duration = this.formatDuration(durationSeconds);
      } else if (job.status === 'running' || job.status === 'scheduled') {
        duration = '...';
      }

      return {
        id: job.id,
        name: taskName,
        queue_id: job.id,
        trace_id: job.id,
        duration,
        finished: this.parseDate(job.ended_at),
        started: this.parseDate(job.started_at),
        status: job.status,
      } as QueuedTask;
    });
  });
  readonly isLoading = this.tasksDataResource.isLoading;

  // Methods
  refreshData() {
    this.tasksDataResource.reload();
  }

  convertTime(seconds: number): string {
    const timeUnits = [
      {unit: 'second', value: 60},
      {unit: 'minute', value: 60},
      {unit: 'hour', value: 24},
      {unit: 'day', value: 7},
    ];

    for (const {unit, value} of timeUnits) {
      if (seconds < value) {
        return `${seconds} ${unit}${seconds === 1 ? '' : 's'}`;
      }
      seconds = Math.floor(seconds / value);
    }
    return `${seconds} ${seconds === 1 ? 'week' : 'weeks'}`;
  }

  formatDuration(duration: number): string {
    if (duration < 1) {
      return '00:00:00';
    }
    const hours = Math.floor(duration / 3600)
      .toString()
      .padStart(2, '0');
    const minutes = Math.floor((duration % 3600) / 60)
      .toString()
      .padStart(2, '0');
    const seconds = Math.floor(duration % 60)
      .toString()
      .padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  }

  private parseDate(dateStr: string | null): Date | null {
    if (!dateStr) return null;
    // Append 'Z' for naive UTC datetimes that lack timezone info
    const normalized = dateStr.endsWith('Z') || dateStr.includes('+') ? dateStr : dateStr + 'Z';
    return new Date(normalized);
  }

  updateTaskConfig(taskKey: string, payload: TaskConfigUpdate): Observable<TaskConfig> {
    return this.http.put<TaskConfig>(this.configsUrl + taskKey, payload);
  }

  runScheduledTask(taskName: string): Observable<string> {
    return this.http.post<string>(this.tasksUrl + taskName + '/run', {});
  }

  pauseTask(taskName: string): Observable<boolean> {
    return this.http.post<boolean>(this.tasksUrl + taskName + '/cancel', {});
  }

  resumeTask(taskName: string): Observable<boolean> {
    return this.http.post<boolean>(this.tasksUrl + taskName + '/resume', {});
  }

  cancelJob(jobId: string): Observable<boolean> {
    return this.http.post<boolean>(this.jobsUrl + jobId + '/cancel', {});
  }
}

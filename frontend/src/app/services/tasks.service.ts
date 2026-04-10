import {HttpClient, httpResource} from '@angular/common/http';
import {computed, inject, Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {environment} from '../../environment';
import {QuivJob, QuivTask, TaskConfig, TaskConfigUpdate, TasksData} from '../models/tasks';

@Injectable({
  providedIn: 'root',
})
export class TasksService {
  private readonly http = inject(HttpClient);

  private taskDataUrl = environment.apiUrl + environment.tasksData;
  private tasksUrl = environment.apiUrl + environment.tasks;
  private jobsUrl = environment.apiUrl + environment.jobs;
  private configsUrl = environment.apiUrl + environment.taskConfigs;

  private readonly tasksDataResource = httpResource<TasksData>(() => this.taskDataUrl, {
    defaultValue: {tasks: [], jobs: [], configs: []},
  });

  readonly scheduledTasks = computed<QuivTask[]>(() => {
    const {tasks, jobs, configs} = this.tasksDataResource.value();

    const lastJobByTaskId = new Map<string, QuivJob>();
    for (const job of jobs) {
      const existing = lastJobByTaskId.get(job.task_id);
      if (!existing || job.started_at > existing.started_at) {
        lastJobByTaskId.set(job.task_id, job);
      }
    }

    const configByName = new Map(configs.map((c) => [c.task_name, c]));

    return tasks.map((task) => ({
      ...task,
      last_run: lastJobByTaskId.get(task.id) ?? null,
      config: configByName.get(task.task_name) ?? null,
    }));
  });

  readonly jobs = computed<QuivJob[]>(() => this.tasksDataResource.value().jobs);
  readonly isLoading = this.tasksDataResource.isLoading;

  refreshData() {
    this.tasksDataResource.reload();
  }

  updateTaskConfig(taskKey: string, taskId: string, payload: TaskConfigUpdate): Observable<TaskConfig> {
    return this.http.put<TaskConfig>(this.configsUrl + taskKey, payload, {params: {task_id: taskId}});
  }

  runScheduledTask(taskId: string): Observable<string> {
    return this.http.post<string>(this.tasksUrl + taskId + '/run', {});
  }

  pauseTask(taskId: string): Observable<boolean> {
    return this.http.post<boolean>(this.tasksUrl + taskId + '/pause', {});
  }

  resumeTask(taskId: string): Observable<boolean> {
    return this.http.post<boolean>(this.tasksUrl + taskId + '/resume', {});
  }

  cancelJob(jobId: string): Observable<boolean> {
    return this.http.post<boolean>(this.jobsUrl + jobId + '/cancel', {});
  }
}

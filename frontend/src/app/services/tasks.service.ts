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

  private readonly latestJobByTaskId = computed<Map<string, QuivJob>>(() => {
    const map = new Map<string, QuivJob>();
    for (const job of this.tasksDataResource.value().jobs) {
      const existing = map.get(job.task_id);
      if (!existing || job.started_at > existing.started_at) {
        map.set(job.task_id, job);
      }
    }
    return map;
  });

  readonly scheduledTasks = computed<QuivTask[]>(() => {
    const {tasks, configs} = this.tasksDataResource.value();
    const lastJobByTaskId = this.latestJobByTaskId();
    const configByName = new Map(configs.map((c) => [c.task_name, c]));
    return tasks.map((task) => ({
      ...task,
      last_run: lastJobByTaskId.get(task.id) ?? null,
      config: configByName.get(task.task_name) ?? null,
    }));
  });

  readonly jobs = computed<QuivJob[]>(() =>
    [...this.latestJobByTaskId().values()].sort(
      (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime(),
    ),
  );
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

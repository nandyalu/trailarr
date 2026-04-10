import {AsyncPipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, ElementRef, inject, signal, viewChild} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {RouterLink} from '@angular/router';
import {RouteLogs} from '../../routing';
import {DurationPipe} from '../helpers/duration.pipe';
import {IntervalPipe} from '../helpers/interval.pipe';
import {TimediffPipe} from '../helpers/timediff.pipe';
import {QuivJob, QuivTask, TaskConfigUpdate} from '../models/tasks';
import {TasksService} from '../services/tasks.service';
import {WebsocketService} from '../services/websocket.service';

@Component({
  selector: 'app-tasks',
  imports: [AsyncPipe, TimediffPipe, IntervalPipe, DurationPipe, RouterLink],
  providers: [],
  templateUrl: './tasks.component.html',
  styleUrl: './tasks.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TasksComponent {
  private readonly tasksService = inject(TasksService);
  private readonly websocketService = inject(WebsocketService);
  private readonly editDialog = viewChild.required<ElementRef<HTMLDialogElement>>('editDialog');

  readonly scheduledTasks = this.tasksService.scheduledTasks;
  readonly jobs = this.tasksService.jobs;
  readonly isLoading = this.tasksService.isLoading;
  editingTask = signal<QuivTask | null>(null);
  isSaving = signal(false);
  protected readonly RouteLogs = RouteLogs;

  constructor() {
    this.websocketService.toastMessage.pipe(takeUntilDestroyed()).subscribe((msg) => {
      if (msg.reload?.includes('tasks')) {
        this.refreshTaskData();
      }
    });
  }

  refreshTaskData() {
    this.tasksService.refreshData();
  }

  runTask(task: QuivTask) {
    this.tasksService.runScheduledTask(task.id).subscribe(() => this.refreshTaskData());
  }

  pauseTask(task: QuivTask) {
    this.tasksService.pauseTask(task.id).subscribe(() => this.refreshTaskData());
  }

  resumeTask(task: QuivTask) {
    this.tasksService.resumeTask(task.id).subscribe(() => this.refreshTaskData());
  }

  cancelJob(job: QuivJob) {
    this.tasksService.cancelJob(job.id).subscribe(() => this.refreshTaskData());
  }

  openEditDialog(task: QuivTask) {
    this.editingTask.set(task);
    this.editDialog().nativeElement.showModal();
  }

  closeEditDialog() {
    this.editDialog().nativeElement.close();
    this.editingTask.set(null);
  }

  saveTaskConfig(name: string, intervalValue: number, intervalUnit: number, delayValue: number, delayUnit: number) {
    const task = this.editingTask();
    if (!task || this.isSaving()) return;

    const payload: TaskConfigUpdate = {
      task_name: name,
      interval_seconds: intervalValue * intervalUnit,
      delay_seconds: delayValue * delayUnit,
    };

    this.isSaving.set(true);
    this.tasksService.updateTaskConfig(task.config?.task_key ?? '', task.id, payload).subscribe({
      next: () => {
        this.isSaving.set(false);
        this.closeEditDialog();
        this.refreshTaskData();
      },
      error: () => {
        this.isSaving.set(false);
      },
    });
  }

  intervalDisplayUnit(seconds: number): number {
    if (seconds >= 86400) return 86400;
    if (seconds >= 3600) return 3600;
    if (seconds >= 60) return 60;
    return 1;
  }

  intervalDisplayValue(seconds: number): number {
    return Math.round(seconds / this.intervalDisplayUnit(seconds));
  }
}

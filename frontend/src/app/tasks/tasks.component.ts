import {AsyncPipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, ElementRef, inject, OnInit, signal, viewChild} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {RouterLink} from '@angular/router';
import {RouteLogs} from '../../routing';
import {TimediffPipe} from '../helpers/timediff.pipe';
import {QueuedTask, ScheduledTask, TaskConfigUpdate} from '../models/tasks';
import {TasksService} from '../services/tasks.service';
import {WebsocketService} from '../services/websocket.service';

@Component({
  selector: 'app-tasks',
  imports: [AsyncPipe, TimediffPipe, RouterLink],
  providers: [],
  templateUrl: './tasks.component.html',
  styleUrl: './tasks.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TasksComponent implements OnInit {
  private readonly tasksService = inject(TasksService);
  private readonly websocketService = inject(WebsocketService);
  private readonly editDialog = viewChild.required<ElementRef<HTMLDialogElement>>('editDialog');

  readonly scheduledTasks = this.tasksService.scheduledTasks;
  readonly queuedTasks = this.tasksService.queuedTasks;
  readonly isLoading = this.tasksService.isLoading;
  editingTask = signal<ScheduledTask | null>(null);
  isSaving = signal(false);
  protected readonly RouteLogs = RouteLogs;

  constructor() {
    this.websocketService.toastMessage.pipe(takeUntilDestroyed()).subscribe((msg) => {
      if (msg.reload?.includes('tasks')) {
        this.refreshTaskData();
      }
    });
  }

  ngOnInit(): void {
    this.refreshTaskData();
  }

  refreshTaskData() {
    this.tasksService.refreshData();
  }

  runTask(task: ScheduledTask) {
    this.tasksService.runScheduledTask(task.task_id).subscribe(() => this.refreshTaskData());
  }

  pauseTask(task: ScheduledTask) {
    this.tasksService.pauseTask(task.task_id).subscribe(() => this.refreshTaskData());
  }

  resumeTask(task: ScheduledTask) {
    this.tasksService.resumeTask(task.task_id).subscribe(() => this.refreshTaskData());
  }

  cancelJob(job: QueuedTask) {
    this.tasksService.cancelJob(job.id).subscribe(() => this.refreshTaskData());
  }

  openEditDialog(task: ScheduledTask) {
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
    this.tasksService.updateTaskConfig(task.task_key, payload).subscribe({
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
}

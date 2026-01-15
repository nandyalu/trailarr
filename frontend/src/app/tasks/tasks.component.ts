import {AsyncPipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, inject, OnInit, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {RouterLink} from '@angular/router';
import {RouteLogs} from 'src/routing';
import {TimediffPipe} from '../helpers/timediff.pipe';
import {QueuedTask, ScheduledTask} from '../models/tasks';
import {TasksService} from '../services/tasks.service';
import {WebsocketService} from '../services/websocket.service';
import {LoadIndicatorComponent} from '../shared/load-indicator';

@Component({
  selector: 'app-tasks',
  imports: [AsyncPipe, LoadIndicatorComponent, TimediffPipe, RouterLink],
  providers: [],
  templateUrl: './tasks.component.html',
  styleUrl: './tasks.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TasksComponent implements OnInit {
  private readonly tasksService = inject(TasksService);
  private readonly websocketService = inject(WebsocketService);

  scheduledTasks = signal<ScheduledTask[]>([]);
  queuedTasks = signal<QueuedTask[]>([]);
  isLoading1 = signal(true);
  isLoading2 = signal(true);
  protected readonly RouteLogs = RouteLogs;

  constructor() {
    // Subscribe to WebSocket toast messages to refresh data on relevant events
    this.websocketService.toastMessage.pipe(takeUntilDestroyed()).subscribe((msg) => {
      if (msg.reload?.includes('tasks')) {
        this.refreshTaskData();
      }
    });
  }

  ngOnInit(): void {
    // On first fetch, get next event start time and set interval to fetch at that time
    this.refreshTaskData();
  }

  refreshTaskData() {
    // Refresh the data
    // console.log('Refreshing task data');
    this.tasksService.getScheduledTasks().subscribe((tasks: ScheduledTask[]) => {
      this.scheduledTasks.set(tasks);
      this.isLoading1.set(false);
    });
    this.tasksService.getQueuedTasks().subscribe((tasks: QueuedTask[]) => {
      this.queuedTasks.set(tasks);
      this.isLoading2.set(false);
    });
  }

  runTask(task_id: string) {
    // console.log('Running task with id:', task_id);
    this.tasksService.runScheduledTask(task_id).subscribe((res: string) => {
      console.log(res);
    });
  }
}

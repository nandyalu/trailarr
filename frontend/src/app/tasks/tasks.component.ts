import {AsyncPipe} from '@angular/common';
import {Component, inject, OnInit} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {TimediffPipe} from '../helpers/timediff.pipe';
import {QueuedTask, ScheduledTask} from '../models/tasks';
import {TasksService} from '../services/tasks.service';
import {WebsocketService} from '../services/websocket.service';
import {LoadIndicatorComponent} from '../shared/load-indicator';

@Component({
  selector: 'app-tasks',
  imports: [AsyncPipe, LoadIndicatorComponent, TimediffPipe],
  providers: [],
  templateUrl: './tasks.component.html',
  styleUrl: './tasks.component.scss',
})
export class TasksComponent implements OnInit {
  private readonly tasksService = inject(TasksService);
  private readonly websocketService = inject(WebsocketService);

  scheduledTasks: ScheduledTask[] = [];
  queuedTasks: QueuedTask[] = [];
  isLoading1 = true;
  isLoading2 = true;

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
    console.log('Refreshing task data');
    this.tasksService.getScheduledTasks().subscribe((tasks: ScheduledTask[]) => {
      this.scheduledTasks = tasks;
      this.isLoading1 = false;
    });
    this.tasksService.getQueuedTasks().subscribe((tasks: QueuedTask[]) => {
      this.queuedTasks = tasks;
      this.isLoading2 = false;
    });
  }

  runTask(task_id: string) {
    // console.log('Running task with id:', task_id);
    this.tasksService.runScheduledTask(task_id).subscribe((res: string) => {
      console.log(res);
    });
  }
}

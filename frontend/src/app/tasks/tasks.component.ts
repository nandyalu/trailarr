import {NgFor, NgIf} from '@angular/common';
import {Component, inject, OnDestroy, OnInit} from '@angular/core';
import {TimeagoModule} from 'ngx-timeago';
import {Subscription} from 'rxjs';
import {QueuedTask, ScheduledTask} from '../models/tasks';
import {TasksService} from '../services/tasks.service';
import {WebsocketService} from '../services/websocket.service';

@Component({
  selector: 'app-tasks',
  imports: [NgIf, NgFor, TimeagoModule],
  providers: [],
  templateUrl: './tasks.component.html',
  styleUrl: './tasks.component.scss',
})
export class TasksComponent implements OnInit, OnDestroy {
  private readonly tasksService = inject(TasksService);
  private readonly websocketService = inject(WebsocketService);

  scheduledTasks: ScheduledTask[] = [];
  queuedTasks: QueuedTask[] = [];
  isLoading1 = true;
  isLoading2 = true;

  private timeoutRef: any;
  private webSocketSubscription?: Subscription;

  ngOnInit(): void {
    // On first fetch, get next event start time and set interval to fetch at that time
    // If a task is running, fetch every 10 seconds
    this.refreshTaskData();

    const handleWebSocketEvent = () => {
      this.refreshTaskData();
    };

    const handleCloseEvent = () => {
      // Unsubscribe from the refresh interval
      clearTimeout(this.timeoutRef);
      // Unsubscribe from the WebSocket events
      this.webSocketSubscription?.unsubscribe();
    };

    // Subscribe to the WebSocket events with the simplified handler
    this.webSocketSubscription = this.websocketService.connect().subscribe({
      next: handleWebSocketEvent,
      error: handleCloseEvent,
      complete: handleCloseEvent,
    });
  }

  getSecondsToNextScheduledEvent(sTasks: ScheduledTask[], qTasks: QueuedTask[]): number {
    // Get the time to the next event
    let secondsToNextEvent = 30; // Default to 30 seconds

    // If an QueuedTask is running, set the time to 10 seconds
    for (let qTask of qTasks) {
      if (qTask.status === 'Running') {
        // console.log('Task is running, wil refresh data in 10 seconds');
        return 10;
      }
    }

    // If no QueuedTask is running, get the time to the next event
    for (let sTask of sTasks) {
      let now = new Date().getTime();
      let nextRun = sTask.next_run.getTime();
      let secondsTillNextRun = Math.floor((nextRun - now) / 1000) + 2;
      secondsTillNextRun = Math.max(secondsTillNextRun, 3); // Ensure that the time is at least 5 second
      if (secondsTillNextRun === 3) {
        // console.log('Task next run soon, will refresh data in 3 seconds');
        return 3;
      }
      secondsToNextEvent = Math.min(secondsToNextEvent, secondsTillNextRun); // Get the minimum time to the next event
    }
    // console.log('No task is running, will refresh data in', secondsToNextEvent, 'seconds');
    return secondsToNextEvent;
  }

  refreshTaskData() {
    // Clear any existing timeout
    clearTimeout(this.timeoutRef);

    // Refresh the data
    // console.log('Refreshing task data');
    this.tasksService.getScheduledTasks().subscribe((tasks: ScheduledTask[]) => {
      this.scheduledTasks = tasks;
      this.isLoading1 = false;
    });
    this.tasksService.getQueuedTasks().subscribe((tasks: QueuedTask[]) => {
      this.queuedTasks = tasks;
      this.isLoading2 = false;
    });

    // Get the time to the next event
    let secondsToNextEvent = this.getSecondsToNextScheduledEvent(this.scheduledTasks, this.queuedTasks);

    // Refresh the data at the time of the next event
    // console.log('Refreshing data in', secondsToNextEvent, 'seconds');
    this.timeoutRef = setTimeout(() => {
      this.refreshTaskData();
    }, secondsToNextEvent * 1000);
  }

  ngOnDestroy() {
    // Unsubscribe from the refresh interval
    clearTimeout(this.timeoutRef);
    // Unsubscribe from the WebSocket events
    this.webSocketSubscription?.unsubscribe();
  }

  runTask(task_id: string) {
    // console.log('Running task with id:', task_id);
    this.tasksService.runScheduledTask(task_id).subscribe((res: string) => {
      console.log(res);
    });
  }
}

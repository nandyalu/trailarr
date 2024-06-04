import { NgFor, NgIf } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { TimeagoIntl, TimeagoModule } from 'ngx-timeago';
import { Subscription, interval, startWith, switchMap } from 'rxjs';
import { QueuedTask, ScheduledTask } from '../models/tasks';
import { TasksService } from '../services/tasks.service';

@Component({
  selector: 'app-tasks',
  standalone: true,
  imports: [NgIf, NgFor, TimeagoModule],
  providers: [TimeagoIntl],
  templateUrl: './tasks.component.html',
  styleUrl: './tasks.component.css'
})
export class TasksComponent implements OnInit, OnDestroy {
  scheduledTasks: ScheduledTask[] = [];
  queuedTasks: QueuedTask[] = [];
  isLoading1 = true;
  isLoading2 = true;

  constructor(private tasksService: TasksService) { }
  // constructor(private tasksService: TasksService, intl: TimeagoIntl) {
  //   // Set the locale to use for timeago
  //   intl.strings = englishStrings;
  //   intl.changes.next();
  //  }

  private scheduledTasksSubscription: Subscription | undefined;
  private queuedTasksSubscription: Subscription | undefined;

  ngOnInit(): void {
    this.scheduledTasksSubscription = interval(10000).pipe(
      startWith(0), // So that it doesn't wait for 3 seconds before the first request
      switchMap(() => this.tasksService.getScheduledTasks())
    ).subscribe((tasks: ScheduledTask[]) => {
      this.scheduledTasks = tasks;
      this.isLoading1 = false;
    });

    this.queuedTasksSubscription = interval(10000).pipe(
      startWith(0), // So that it doesn't wait for 3 seconds before the first request
      switchMap(() => this.tasksService.getQueuedTasks())
    ).subscribe((tasks: QueuedTask[]) => {
      this.queuedTasks = tasks;
      this.isLoading2 = false;
    });
  }

  ngOnDestroy(): void {
    // Unsubscribe from the interval
    this.scheduledTasksSubscription?.unsubscribe();
    this.queuedTasksSubscription?.unsubscribe();
  }

  runTask(id: number) {
    console.log('Running task with id:', id);
    // TODO: Implement the runTask method
  }

  // ngOnInit(): void {
  //   this.isLoading1 = true;
  //   this.isLoading2 = true;
  //   this.tasksService.getScheduledTasks().subscribe((tasks: ScheduledTask[]) => {
  //     this.scheduledTasks = tasks;
  //     this.isLoading1 = false;
  //   });
  //   this.tasksService.getQueuedTasks().subscribe((tasks: QueuedTask[]) => {
  //     this.queuedTasks = tasks;
  //     this.isLoading2 = false;
  //   });
  // }

}

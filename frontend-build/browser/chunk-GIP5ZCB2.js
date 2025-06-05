import {
  WebsocketService
} from "./chunk-KIVIDEQ5.js";
import {
  TimeagoModule,
  TimeagoPipe
} from "./chunk-F6W3V265.js";
import {
  LoadIndicatorComponent
} from "./chunk-7SOVNULQ.js";
import {
  Component,
  HttpClient,
  Injectable,
  NgForOf,
  NgIf,
  __spreadProps,
  __spreadValues,
  environment,
  inject,
  map,
  setClassMetadata,
  ɵsetClassDebugInfo,
  ɵɵProvidersFeature,
  ɵɵadvance,
  ɵɵdefineComponent,
  ɵɵdefineInjectable,
  ɵɵelement,
  ɵɵelementEnd,
  ɵɵelementStart,
  ɵɵgetCurrentView,
  ɵɵlistener,
  ɵɵnamespaceSVG,
  ɵɵnextContext,
  ɵɵpipe,
  ɵɵpipeBind1,
  ɵɵproperty,
  ɵɵreference,
  ɵɵresetView,
  ɵɵrestoreView,
  ɵɵtemplate,
  ɵɵtemplateRefExtractor,
  ɵɵtext,
  ɵɵtextInterpolate
} from "./chunk-FAGZ4ZSE.js";

// src/app/services/tasks.service.ts
var TasksService = class _TasksService {
  constructor() {
    this.http = inject(HttpClient);
    this.tasksUrl = environment.apiUrl + environment.tasks;
    this.schedulesUrl = this.tasksUrl + "schedules";
    this.queueUrl = this.tasksUrl + "queue";
  }
  convertTime(seconds) {
    const timeUnits = [
      { unit: "second", value: 60 },
      { unit: "minute", value: 60 },
      { unit: "hour", value: 24 },
      { unit: "day", value: 7 }
    ];
    for (const { unit, value } of timeUnits) {
      if (seconds < value) {
        return `${seconds} ${unit}${seconds === 1 ? "" : "s"}`;
      }
      seconds = Math.floor(seconds / value);
    }
    return `${seconds} ${seconds === 1 ? "week" : "weeks"}`;
  }
  convertDate(date) {
    return date ? /* @__PURE__ */ new Date(date + "Z") : null;
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
  formatDuration(duration) {
    if (duration < 1) {
      return "00:00:00";
    }
    let hours = Math.floor(duration / 3600).toString().padStart(2, "0");
    let minutes = Math.floor(duration % 3600 / 60).toString().padStart(2, "0");
    let seconds = (duration % 60).toString().padStart(2, "0");
    return `${hours}:${minutes}:${seconds}`;
  }
  getScheduledTasks() {
    return this.http.get(this.schedulesUrl).pipe(map((all_schedules) => {
      return Object.entries(all_schedules).map(([id, schedule]) => __spreadProps(__spreadValues({
        id
      }, schedule), {
        interval: this.convertTime(schedule.interval),
        last_run_duration: this.formatDuration(schedule.last_run_duration),
        last_run_start: this.convertDate(schedule.last_run_start),
        next_run: this.convertDate(schedule.next_run)
      }));
    }));
  }
  getQueuedTasks() {
    return this.http.get(this.queueUrl).pipe(map((all_queues) => {
      return Object.entries(all_queues).map(([id, queue]) => __spreadProps(__spreadValues({
        id
      }, queue), {
        duration: this.formatDuration(queue.duration),
        finished: this.convertDate(queue.finished),
        started: this.convertDate(queue.started)
        // end: this.convertDate(queue.end)
      }));
    }));
  }
  runScheduledTask(id) {
    return this.http.get(this.tasksUrl + "run/" + id);
  }
  static {
    this.\u0275fac = function TasksService_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _TasksService)();
    };
  }
  static {
    this.\u0275prov = /* @__PURE__ */ \u0275\u0275defineInjectable({ token: _TasksService, factory: _TasksService.\u0275fac, providedIn: "root" });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(TasksService, [{
    type: Injectable,
    args: [{
      providedIn: "root"
    }]
  }], null, null);
})();

// src/app/tasks/tasks.component.ts
function TasksComponent_app_load_indicator_4_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "app-load-indicator", 5);
  }
}
function TasksComponent_ng_template_5_tr_16_td_15_Template(rf, ctx) {
  if (rf & 1) {
    const _r1 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "td", 14);
    \u0275\u0275listener("click", function TasksComponent_ng_template_5_tr_16_td_15_Template_td_click_0_listener() {
      \u0275\u0275restoreView(_r1);
      const task_r2 = \u0275\u0275nextContext().$implicit;
      const ctx_r2 = \u0275\u0275nextContext(2);
      task_r2.last_run_status = "Running";
      return \u0275\u0275resetView(ctx_r2.runTask(task_r2.task_id));
    });
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(1, "svg", 15);
    \u0275\u0275element(2, "path", 16);
    \u0275\u0275elementEnd()();
  }
}
function TasksComponent_ng_template_5_tr_16_td_16_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "td", 17);
    \u0275\u0275namespaceSVG();
    \u0275\u0275elementStart(1, "svg", 18);
    \u0275\u0275element(2, "path", 19);
    \u0275\u0275elementEnd()();
  }
}
function TasksComponent_ng_template_5_tr_16_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "tr", 11)(1, "td", 9);
    \u0275\u0275text(2);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "td");
    \u0275\u0275text(4);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(5, "td");
    \u0275\u0275text(6);
    \u0275\u0275pipe(7, "timeago");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(8, "td");
    \u0275\u0275text(9);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(10, "td");
    \u0275\u0275text(11);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(12, "td");
    \u0275\u0275text(13);
    \u0275\u0275pipe(14, "timeago");
    \u0275\u0275elementEnd();
    \u0275\u0275template(15, TasksComponent_ng_template_5_tr_16_td_15_Template, 3, 0, "td", 12)(16, TasksComponent_ng_template_5_tr_16_td_16_Template, 3, 0, "td", 13);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const task_r2 = ctx.$implicit;
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(task_r2.name);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(task_r2.interval);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(task_r2.last_run_start ? \u0275\u0275pipeBind1(7, 8, task_r2.last_run_start) : "Not run yet");
    \u0275\u0275advance(3);
    \u0275\u0275textInterpolate(task_r2.last_run_status);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(task_r2.last_run_duration);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(task_r2.next_run ? \u0275\u0275pipeBind1(14, 10, task_r2.next_run) : "Not scheduled");
    \u0275\u0275advance(2);
    \u0275\u0275property("ngIf", task_r2.last_run_status.toLowerCase() != "running");
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", task_r2.last_run_status.toLowerCase() == "running");
  }
}
function TasksComponent_ng_template_5_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 6)(1, "table", 7)(2, "tr", 8)(3, "th", 9);
    \u0275\u0275text(4, "Name");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(5, "th");
    \u0275\u0275text(6, "Interval");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(7, "th");
    \u0275\u0275text(8, "Last Run");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(9, "th");
    \u0275\u0275text(10, "Last Run Status");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(11, "th");
    \u0275\u0275text(12, "Last Run Duration");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(13, "th");
    \u0275\u0275text(14, "Next Run");
    \u0275\u0275elementEnd();
    \u0275\u0275element(15, "th");
    \u0275\u0275elementEnd();
    \u0275\u0275template(16, TasksComponent_ng_template_5_tr_16_Template, 17, 12, "tr", 10);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext();
    \u0275\u0275advance(16);
    \u0275\u0275property("ngForOf", ctx_r2.scheduledTasks);
  }
}
function TasksComponent_app_load_indicator_10_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "app-load-indicator", 5);
  }
}
function TasksComponent_ng_template_11_tr_13_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "tr", 11)(1, "td", 9);
    \u0275\u0275text(2);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(3, "td");
    \u0275\u0275text(4);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(5, "td");
    \u0275\u0275text(6);
    \u0275\u0275pipe(7, "timeago");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(8, "td");
    \u0275\u0275text(9);
    \u0275\u0275pipe(10, "timeago");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(11, "td");
    \u0275\u0275text(12);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const task_r4 = ctx.$implicit;
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(task_r4.name);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(task_r4.status);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(task_r4.started ? \u0275\u0275pipeBind1(7, 5, task_r4.started) : "Pending");
    \u0275\u0275advance(3);
    \u0275\u0275textInterpolate(task_r4.finished ? \u0275\u0275pipeBind1(10, 7, task_r4.finished) : "-");
    \u0275\u0275advance(3);
    \u0275\u0275textInterpolate(task_r4.duration);
  }
}
function TasksComponent_ng_template_11_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "div", 20)(1, "table", 7)(2, "tr", 8)(3, "th", 9);
    \u0275\u0275text(4, "Name");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(5, "th");
    \u0275\u0275text(6, "Status");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(7, "th");
    \u0275\u0275text(8, "Started");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(9, "th");
    \u0275\u0275text(10, "Finished");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(11, "th");
    \u0275\u0275text(12, "Duration");
    \u0275\u0275elementEnd()();
    \u0275\u0275template(13, TasksComponent_ng_template_11_tr_13_Template, 13, 9, "tr", 10);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext();
    \u0275\u0275advance(13);
    \u0275\u0275property("ngForOf", ctx_r2.queuedTasks);
  }
}
var TasksComponent = class _TasksComponent {
  constructor() {
    this.tasksService = inject(TasksService);
    this.websocketService = inject(WebsocketService);
    this.scheduledTasks = [];
    this.queuedTasks = [];
    this.isLoading1 = true;
    this.isLoading2 = true;
  }
  ngOnInit() {
    this.refreshTaskData();
    const handleWebSocketEvent = () => {
      this.refreshTaskData();
    };
    const handleCloseEvent = () => {
      clearTimeout(this.timeoutRef);
      this.webSocketSubscription?.unsubscribe();
    };
    this.webSocketSubscription = this.websocketService.connect().subscribe({
      next: handleWebSocketEvent,
      error: handleCloseEvent,
      complete: handleCloseEvent
    });
  }
  getSecondsToNextScheduledEvent(sTasks, qTasks) {
    let secondsToNextEvent = 30;
    for (let qTask of qTasks) {
      if (qTask.status === "Running") {
        return 10;
      }
    }
    for (let sTask of sTasks) {
      let now = (/* @__PURE__ */ new Date()).getTime();
      let nextRun = sTask.next_run.getTime();
      let secondsTillNextRun = Math.floor((nextRun - now) / 1e3) + 2;
      secondsTillNextRun = Math.max(secondsTillNextRun, 3);
      if (secondsTillNextRun === 3) {
        return 3;
      }
      secondsToNextEvent = Math.min(secondsToNextEvent, secondsTillNextRun);
    }
    return secondsToNextEvent;
  }
  refreshTaskData() {
    clearTimeout(this.timeoutRef);
    this.tasksService.getScheduledTasks().subscribe((tasks) => {
      this.scheduledTasks = tasks;
      this.isLoading1 = false;
    });
    this.tasksService.getQueuedTasks().subscribe((tasks) => {
      this.queuedTasks = tasks;
      this.isLoading2 = false;
    });
    let secondsToNextEvent = this.getSecondsToNextScheduledEvent(this.scheduledTasks, this.queuedTasks);
    this.timeoutRef = setTimeout(() => {
      this.refreshTaskData();
    }, secondsToNextEvent * 1e3);
  }
  ngOnDestroy() {
    clearTimeout(this.timeoutRef);
    this.webSocketSubscription?.unsubscribe();
  }
  runTask(task_id) {
    this.tasksService.runScheduledTask(task_id).subscribe((res) => {
      console.log(res);
    });
  }
  static {
    this.\u0275fac = function TasksComponent_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _TasksComponent)();
    };
  }
  static {
    this.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _TasksComponent, selectors: [["app-tasks"]], features: [\u0275\u0275ProvidersFeature([])], decls: 13, vars: 4, consts: [["schedulesLoaded", ""], ["queueLoaded", ""], [1, "tasks-container"], [1, "text-heading"], ["class", "center", 4, "ngIf", "ngIfElse"], [1, "center"], [1, "table-container"], [1, "tasks-table"], [1, "table-row", "header"], [1, "name"], ["class", "table-row", 4, "ngFor", "ngForOf"], [1, "table-row"], ["title", "Run task now", 3, "click", 4, "ngIf"], ["title", "Task is running", 4, "ngIf"], ["title", "Run task now", 3, "click"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960"], ["d", "M382-306.67 653.33-480 382-653.33v346.66ZM480-80q-82.33 0-155.33-31.5-73-31.5-127.34-85.83Q143-251.67 111.5-324.67T80-480q0-83 31.5-156t85.83-127q54.34-54 127.34-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 82.33-31.5 155.33-31.5 73-85.5 127.34Q709-143 636-111.5T480-80Z"], ["title", "Task is running"], ["xmlns", "http://www.w3.org/2000/svg", "viewBox", "0 -960 960 960", 1, "loading"], ["d", "M343-107q-120-42-194.5-146.5T74-490q0-29 4-57.5T91-604l-57 33-37-62 185-107 106 184-63 36-54-92q-13 30-18.5 60.5T147-490q0 113 65.5 200T381-171l-38 64Zm291-516v-73h107q-47-60-115.5-93.5T480-823q-66 0-123.5 24T255-734l-38-65q54-45 121-71t142-26q85 0 160.5 33T774-769v-67h73v213H634ZM598-1 413-107l107-184 62 37-54 94q123-17 204.5-110.5T814-489q0-19-2.5-37.5T805-563h74q4 18 6 36.5t2 36.5q0 142-87 251.5T578-96l56 33-36 62Z"], [1, "table-container", "last-table"]], template: function TasksComponent_Template(rf, ctx) {
      if (rf & 1) {
        \u0275\u0275elementStart(0, "div", 2)(1, "div", 3);
        \u0275\u0275text(2, "Scheduled");
        \u0275\u0275elementEnd();
        \u0275\u0275element(3, "hr");
        \u0275\u0275template(4, TasksComponent_app_load_indicator_4_Template, 1, 0, "app-load-indicator", 4)(5, TasksComponent_ng_template_5_Template, 17, 1, "ng-template", null, 0, \u0275\u0275templateRefExtractor);
        \u0275\u0275elementStart(7, "div", 3);
        \u0275\u0275text(8, "Queue");
        \u0275\u0275elementEnd();
        \u0275\u0275element(9, "hr");
        \u0275\u0275template(10, TasksComponent_app_load_indicator_10_Template, 1, 0, "app-load-indicator", 4)(11, TasksComponent_ng_template_11_Template, 14, 1, "ng-template", null, 1, \u0275\u0275templateRefExtractor);
        \u0275\u0275elementEnd();
      }
      if (rf & 2) {
        const schedulesLoaded_r5 = \u0275\u0275reference(6);
        const queueLoaded_r6 = \u0275\u0275reference(12);
        \u0275\u0275advance(4);
        \u0275\u0275property("ngIf", ctx.isLoading1)("ngIfElse", schedulesLoaded_r5);
        \u0275\u0275advance(6);
        \u0275\u0275property("ngIf", ctx.isLoading1)("ngIfElse", queueLoaded_r6);
      }
    }, dependencies: [NgIf, NgForOf, LoadIndicatorComponent, TimeagoModule, TimeagoPipe], styles: ["\n\n.tasks-container[_ngcontent-%COMP%] {\n  display: flex;\n  flex-direction: column;\n  padding: 1rem;\n}\n@media (width < 765px) {\n  .tasks-container[_ngcontent-%COMP%] {\n    padding: 0.5rem;\n  }\n}\n.text-heading[_ngcontent-%COMP%] {\n  margin-top: 1rem;\n  text-align: left;\n  font-size: 2rem;\n}\n.center[_ngcontent-%COMP%] {\n  margin: auto;\n}\n.table-container[_ngcontent-%COMP%] {\n  width: 100%;\n  overflow-x: auto;\n  min-height: 25%;\n  -webkit-overflow-scrolling: touch;\n  margin-top: 0.5rem;\n  margin-bottom: 2rem;\n}\n.last-table[_ngcontent-%COMP%] {\n  margin-bottom: 0;\n}\n.tasks-table[_ngcontent-%COMP%] {\n  width: 100%;\n  max-width: 100%;\n  white-space: nowrap;\n  border-collapse: collapse;\n}\n.tasks-table[_ngcontent-%COMP%]   .table-row[_ngcontent-%COMP%] {\n  border-bottom: 1px solid var(--color-outline);\n  white-space: nowrap;\n  text-align: left;\n}\n.tasks-table[_ngcontent-%COMP%]   th[_ngcontent-%COMP%], \n.tasks-table[_ngcontent-%COMP%]   td[_ngcontent-%COMP%] {\n  padding: 1rem 0.5rem;\n}\n.tasks-table[_ngcontent-%COMP%]   .header[_ngcontent-%COMP%] {\n  font-weight: bold;\n  border-bottom: 2px solid var(--color-outline);\n}\n.tasks-table[_ngcontent-%COMP%]   .name[_ngcontent-%COMP%] {\n  width: 100%;\n}\n.table-row[_ngcontent-%COMP%]   svg[_ngcontent-%COMP%] {\n  margin: 0 0.5rem;\n  width: 1rem;\n  fill: var(--color-primary);\n  cursor: pointer;\n}\n.loading[_ngcontent-%COMP%] {\n  cursor: progress;\n  animation: spin-animation 2s linear infinite;\n}\n.table-row[_ngcontent-%COMP%]:hover:not(:first-child) {\n  background-color: var(--color-tertiary-container);\n}\n/*# sourceMappingURL=tasks.component.css.map */"] });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(TasksComponent, [{
    type: Component,
    args: [{ selector: "app-tasks", imports: [NgIf, NgForOf, LoadIndicatorComponent, TimeagoModule], providers: [], template: `<div class="tasks-container">
  <div class="text-heading">Scheduled</div>
  <hr />
  <app-load-indicator *ngIf="isLoading1; else schedulesLoaded" class="center" />
  <ng-template #schedulesLoaded>
    <div class="table-container">
      <table class="tasks-table">
        <tr class="table-row header">
          <th class="name">Name</th>
          <th>Interval</th>
          <th>Last Run</th>
          <th>Last Run Status</th>
          <th>Last Run Duration</th>
          <th>Next Run</th>
          <th></th>
        </tr>
        <!-- <p>{{ scheduledTasks }}</p> -->
        <tr *ngFor="let task of scheduledTasks" class="table-row">
          <!-- <td class="name">{{ task.id }}: {{ task.name }}</td> -->
          <td class="name">{{ task.name }}</td>
          <td>{{ task.interval }}</td>
          <td>{{ task.last_run_start ? (task.last_run_start | timeago) : 'Not run yet' }}</td>
          <td>{{ task.last_run_status }}</td>
          <td>{{ task.last_run_duration }}</td>
          <td>{{ task.next_run ? (task.next_run | timeago) : 'Not scheduled' }}</td>
          <td
            *ngIf="task.last_run_status.toLowerCase() != 'running'"
            title="Run task now"
            (click)="task.last_run_status = 'Running'; runTask(task.task_id)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
              <path
                d="M382-306.67 653.33-480 382-653.33v346.66ZM480-80q-82.33 0-155.33-31.5-73-31.5-127.34-85.83Q143-251.67 111.5-324.67T80-480q0-83 31.5-156t85.83-127q54.34-54 127.34-85.5T480-880q83 0 156 31.5T763-763q54 54 85.5 127T880-480q0 82.33-31.5 155.33-31.5 73-85.5 127.34Q709-143 636-111.5T480-80Z"
              />
            </svg>
          </td>
          <td *ngIf="task.last_run_status.toLowerCase() == 'running'" title="Task is running">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960" class="loading">
              <path
                d="M343-107q-120-42-194.5-146.5T74-490q0-29 4-57.5T91-604l-57 33-37-62 185-107 106 184-63 36-54-92q-13 30-18.5 60.5T147-490q0 113 65.5 200T381-171l-38 64Zm291-516v-73h107q-47-60-115.5-93.5T480-823q-66 0-123.5 24T255-734l-38-65q54-45 121-71t142-26q85 0 160.5 33T774-769v-67h73v213H634ZM598-1 413-107l107-184 62 37-54 94q123-17 204.5-110.5T814-489q0-19-2.5-37.5T805-563h74q4 18 6 36.5t2 36.5q0 142-87 251.5T578-96l56 33-36 62Z"
              />
            </svg>
          </td>
        </tr>
      </table>
    </div>
  </ng-template>
  <div class="text-heading">Queue</div>
  <hr />
  <app-load-indicator *ngIf="isLoading1; else queueLoaded" class="center" />
  <ng-template #queueLoaded>
    <div class="table-container last-table">
      <table class="tasks-table">
        <tr class="table-row header">
          <th class="name">Name</th>
          <th>Status</th>
          <th>Started</th>
          <th>Finished</th>
          <th>Duration</th>
        </tr>
        <!-- <p>{{ queuedTasks }}</p> -->
        <tr *ngFor="let task of queuedTasks" class="table-row">
          <!-- <td class="name">{{ task.id }}: {{ task.name }}</td> -->
          <td class="name">{{ task.name }}</td>
          <td>{{ task.status }}</td>
          <td>{{ task.started ? (task.started | timeago) : 'Pending' }}</td>
          <td>{{ task.finished ? (task.finished | timeago) : '-' }}</td>
          <td>{{ task.duration }}</td>
        </tr>
      </table>
    </div>
  </ng-template>
</div>
`, styles: ["/* src/app/tasks/tasks.component.scss */\n.tasks-container {\n  display: flex;\n  flex-direction: column;\n  padding: 1rem;\n}\n@media (width < 765px) {\n  .tasks-container {\n    padding: 0.5rem;\n  }\n}\n.text-heading {\n  margin-top: 1rem;\n  text-align: left;\n  font-size: 2rem;\n}\n.center {\n  margin: auto;\n}\n.table-container {\n  width: 100%;\n  overflow-x: auto;\n  min-height: 25%;\n  -webkit-overflow-scrolling: touch;\n  margin-top: 0.5rem;\n  margin-bottom: 2rem;\n}\n.last-table {\n  margin-bottom: 0;\n}\n.tasks-table {\n  width: 100%;\n  max-width: 100%;\n  white-space: nowrap;\n  border-collapse: collapse;\n}\n.tasks-table .table-row {\n  border-bottom: 1px solid var(--color-outline);\n  white-space: nowrap;\n  text-align: left;\n}\n.tasks-table th,\n.tasks-table td {\n  padding: 1rem 0.5rem;\n}\n.tasks-table .header {\n  font-weight: bold;\n  border-bottom: 2px solid var(--color-outline);\n}\n.tasks-table .name {\n  width: 100%;\n}\n.table-row svg {\n  margin: 0 0.5rem;\n  width: 1rem;\n  fill: var(--color-primary);\n  cursor: pointer;\n}\n.loading {\n  cursor: progress;\n  animation: spin-animation 2s linear infinite;\n}\n.table-row:hover:not(:first-child) {\n  background-color: var(--color-tertiary-container);\n}\n/*# sourceMappingURL=tasks.component.css.map */\n"] }]
  }], null, null);
})();
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(TasksComponent, { className: "TasksComponent", filePath: "src/app/tasks/tasks.component.ts", lineNumber: 17 });
})();

// src/app/tasks/routes.ts
var routes_default = [{ path: "", loadComponent: () => TasksComponent }];
export {
  routes_default as default
};
//# sourceMappingURL=chunk-GIP5ZCB2.js.map

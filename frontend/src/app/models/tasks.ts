export interface QuivTask {
  id: string;
  task_name: string;
  args: string;
  kwargs: string;
  interval_seconds: number;
  run_once: boolean;
  status: string;
  next_run_at: string | null;
}

export interface QuivJob {
  id: string;
  task_id: string;
  status: string;
  started_at: string;
  ended_at: string | null;
}

export interface TaskConfig {
  id: number;
  task_key: string;
  task_name: string;
  interval_seconds: number;
  delay_seconds: number;
}

export interface TasksData {
  tasks: QuivTask[];
  jobs: QuivJob[];
  configs: TaskConfig[];
}

export interface TaskConfigUpdate {
  task_name: string;
  interval_seconds: number;
  delay_seconds: number;
}

export interface ScheduledTask {
  id: string;
  name: string;
  task_id: string;
  task_key: string;
  task_status: string;
  interval: string;
  interval_seconds: number;
  delay_seconds: number;
  last_run_duration: string;
  last_run_start: Date | null;
  last_run_status: string;
  next_run: Date | null;
}

export interface QueuedTask {
  id: string;
  name: string;
  queue_id: string;
  trace_id: string;
  duration: string;
  finished: Date | null;
  started: Date | null;
  status: string;
}

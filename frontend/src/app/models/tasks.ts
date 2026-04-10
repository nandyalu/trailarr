export interface QuivTask {
  id: string;
  task_name: string;
  args: string;
  kwargs: string;
  interval_seconds: number;
  run_once: boolean;
  status: string;
  next_run_at: string | null;
  last_run: QuivJob | null;
  config: TaskConfig | null;
}

export interface QuivJob {
  id: string;
  task_id: string;
  task_name: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
  error_message: string | null;
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

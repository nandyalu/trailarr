
export interface ScheduledTask {
    id: number;
    name: string;
    task_id: string;
    interval: number;
    last_run_duration: number;
    last_run_start: Date;
    last_run_status: string;
    next_run: Date;
}

export interface QueuedTask {
    id: number;
    name: string;
    queue_id: string;
    duration: number;
    finished: Date;
    started: Date;
    status: string;
    // end: Date;
} 
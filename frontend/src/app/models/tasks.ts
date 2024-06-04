
export interface ScheduledTask {
    id: number;
    name: string;
    interval: number;
    last_run_status: string;
    last_run_start: Date;
    last_run_duration: string;
    next_run: Date;
}

export interface QueuedTask {
    id: number;
    name: string;
    status: string;
    queued: Date;
    start: Date;
    end: Date;
    duration: string;
}
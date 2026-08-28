import {ProbeStatus} from './diagnostics';

export interface HealthCheckResult {
  key: string;
  name: string;
  status: ProbeStatus;
  detail: string;
  remediation: string;
  docs_url: string;
  checked_at: string;
}

export interface HealthReport {
  checked_at: string;
  status: 'healthy' | 'issues';
  checks: HealthCheckResult[];
}

export interface CookiesStatus {
  configured: boolean;
  path: string;
  exists: boolean;
  youtube_cookies: number;
  expired: boolean;
  detail: string;
}

export type ProbeStatus = 'ok' | 'warning' | 'error' | 'skipped';

export interface SuggestedMapping {
  path_from: string;
  path_to: string;
  /** Number of probed paths that resolve under this mapping. 1 means the
   * match is based on the folder name only — check before applying. */
  corroborations: number;
}

export interface ProbeResult {
  kind: 'reachability' | 'path_visibility' | 'permissions' | 'path_style';
  name: string;
  status: ProbeStatus;
  detail: string;
  remediation: string;
  docs_url: string;
  suggested_mapping: SuggestedMapping | null;
}

export interface DoctorReport {
  connection_id: number;
  connection_name: string;
  checked_at: string;
  status: 'healthy' | 'issues';
  probes: ProbeResult[];
}

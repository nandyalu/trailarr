export type IssueType = 'file_deleted' | 'connection_failed' | 'token_invalid' | 'folder_missing';

export type EntityType = 'media_trailer_status' | 'connection' | 'download';

export interface Issue {
  id: number;
  issue_type: IssueType;
  entity_type: EntityType;
  entity_id: number;
  description: string;
  details: string | null;
  entity_name: string | null;
  created_at: string;
  updated_at: string;
}

/** Returns true if any issue requires urgent attention (auth/connection problems). */
export function hasUrgentIssues(issues: Issue[]): boolean {
  return issues.some((i) => i.issue_type === 'connection_failed' || i.issue_type === 'token_invalid');
}

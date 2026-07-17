import {parseDate} from './media';

/** One row of the per-media download-profile matrix (Phase 3).
 * Mirrors the backend's MediaPendingProfile — computed with the exact
 * satisfaction rule the download task uses. */
export interface MediaPendingProfile {
  profile_id: number;
  profile_name: string;
  enabled: boolean;
  matches: boolean;
  satisfied: boolean;
  satisfied_by: number | null; // download id
  satisfied_via: 'own_download' | 'claim' | 'stop_monitoring' | null;
  pending: boolean;
  backing_off: boolean;
  attempt_count: number;
  last_error: string | null;
  next_eligible_at: Date | null;
}

export interface MediaPendingView {
  media_id: number;
  monitor: boolean;
  profiles: MediaPendingProfile[];
}

export function mapMediaPending(view: any): MediaPendingView {
  return {
    ...view,
    profiles: (view.profiles ?? []).map((profile: any) => ({
      ...profile,
      next_eligible_at: profile.next_eligible_at ? parseDate(profile.next_eligible_at) : null,
    })),
  };
}

/** One (media, profile) pair from the library-wide pending summary. */
export interface PendingSummaryItem {
  media_id: number;
  title: string;
  is_movie: boolean;
  profile_id: number;
  profile_name: string;
  reason: 'pending' | 'backoff';
  next_eligible_at: Date | null;
}

/** Library-wide preview of the download task's work list. */
export interface PendingSummary {
  total_media: number;
  pending_pairs: number;
  backoff_pairs: number;
  items: PendingSummaryItem[];
  limit: number;
  offset: number;
}

export function mapPendingSummary(summary: any): PendingSummary {
  return {
    ...summary,
    items: (summary.items ?? []).map((item: any) => ({
      ...item,
      next_eligible_at: item.next_eligible_at ? parseDate(item.next_eligible_at) : null,
    })),
  };
}

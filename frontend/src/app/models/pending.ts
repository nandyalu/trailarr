import {parseDate} from './media';

/** Why Upgrade To TMDB Trailer replaces a trailer, or why it keeps it.
 * Mirrors the backend's UpgradeState; null when the upgrade is off or inert. */
export type UpgradeState = 'replace_not_tmdb' | 'replace_unknown' | 'matched' | 'awaiting_tmdb' | 'unknown_kept';

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
  satisfied_via: 'own_download' | 'claim' | null;
  pending: boolean;
  /** Pending only because Upgrade To TMDB Trailer replaces the trailer. */
  upgrade: boolean;
  upgrade_state: UpgradeState | null;
  backing_off: boolean;
  attempt_count: number;
  last_error: string | null;
  next_eligible_at: Date | null;
}

export interface MediaPendingView {
  media_id: number;
  monitor: boolean;
  /** An upgrade that waits for TMDB reads differently when the item has no
   * TMDB id, when TMDB was not asked yet, and when it listed nothing. */
  has_tmdb_id: boolean;
  tmdb_asked: boolean;
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
  /** The trailer is on disk, and the download replaces it with a TMDB one. */
  upgrade: boolean;
  upgrade_state: UpgradeState | null;
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

/** One (media, profile) pair whose downloads keep failing — GET /media/failing.
 * Drives the review banner and the 'Failing Downloads' quick filter. */
export interface FailingDownload {
  media_id: number;
  title: string;
  is_movie: boolean;
  profile_id: number;
  profile_name: string;
  attempt_count: number;
  /** The reason of the last failure, with the fix when Trailarr knows it. */
  last_error: string | null;
  next_eligible_at: Date;
  /** The trailer is on disk, and the failing download replaces it. */
  upgrade: boolean;
}

export function mapFailingDownloads(items: any[]): FailingDownload[] {
  return (items ?? []).map((item: any) => ({
    ...item,
    next_eligible_at: parseDate(item.next_eligible_at),
  }));
}

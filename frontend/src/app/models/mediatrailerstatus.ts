export type VideoType = 'trailer' | 'teaser' | 'clip' | 'behind the scenes' | 'bloopers' | 'featurette' | 'opening credits';

export type TrailerStatusEnum =
  | 'pending'
  | 'downloading'
  | 'downloaded'
  | 'failed'
  | 'skipped'
  | 'unmonitored'
  | 'not_available';

export type TrailerSourceEnum = 'app' | 'manual';

export interface MediaTrailerStatus {
  id: number;
  media_id: number;
  profile_id: number | null;
  profile_name: string | null;
  video_type: VideoType | null;
  season: number;
  sequence: number;
  status: TrailerStatusEnum;
  source: TrailerSourceEnum;
  linked_download_id: number | null;
  created_at: string;
  updated_at: string;
}

export function buildTrailerStatusMap(rows: MediaTrailerStatus[]): Map<number, MediaTrailerStatus[]> {
  const map = new Map<number, MediaTrailerStatus[]>();
  for (const row of rows) {
    if (!map.has(row.media_id)) {
      map.set(row.media_id, []);
    }
    map.get(row.media_id)!.push(row);
  }
  return map;
}

/** Returns true if any row has status=downloaded AND video_type=trailer (or null, for unattributed). */
export function computeTrailerExists(statuses: MediaTrailerStatus[]): boolean {
  return statuses.some(
    (s) => s.status === 'downloaded' && (s.video_type === 'trailer' || s.video_type === null),
  );
}

/** Derives the legacy MonitorStatus string from per-profile rows + monitor flag. */
export function computeMonitorStatus(statuses: MediaTrailerStatus[], monitor: boolean): string {
  if (statuses.some((s) => s.status === 'downloading')) return 'Downloading';
  if (statuses.some((s) => s.status === 'downloaded')) return 'Downloaded';
  if (monitor && statuses.some((s) => s.status === 'pending')) return 'Monitored';
  return 'Missing';
}

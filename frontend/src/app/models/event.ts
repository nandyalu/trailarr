export enum EventType {
  MEDIA_ADDED = 'media_added',
  MONITOR_CHANGED = 'monitor_changed',
  YOUTUBE_ID_CHANGED = 'youtube_id_changed',
  TRAILER_DETECTED = 'trailer_detected',
  TRAILER_DOWNLOADED = 'trailer_downloaded',
  TRAILER_DELETED = 'trailer_deleted',
  DOWNLOAD_SKIPPED = 'download_skipped',
  PLEX_LINKED = 'plex_linked',
  PLEX_UNLINKED = 'plex_unlinked',
  PLEX_SCAN_TRIGGERED = 'plex_scan_triggered',
}

export enum EventSource {
  USER = 'user',
  SYSTEM = 'system',
}

export interface EventRead {
  id: number;
  media_id: number;
  event_type: EventType;
  source: EventSource;
  source_detail: string;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
}

export const EVENT_TYPE_LABELS: Record<EventType, string> = {
  [EventType.MEDIA_ADDED]: 'Media Added',
  [EventType.MONITOR_CHANGED]: 'Monitor Changed',
  [EventType.YOUTUBE_ID_CHANGED]: 'YouTube ID Changed',
  [EventType.TRAILER_DETECTED]: 'Trailer Detected',
  [EventType.TRAILER_DOWNLOADED]: 'Trailer Downloaded',
  [EventType.TRAILER_DELETED]: 'Trailer Deleted',
  [EventType.DOWNLOAD_SKIPPED]: 'Download Skipped',
  [EventType.PLEX_LINKED]: 'Plex Linked',
  [EventType.PLEX_UNLINKED]: 'Plex Unlinked',
  [EventType.PLEX_SCAN_TRIGGERED]: 'Plex Scan Triggered',
};

export const EVENT_SOURCE_LABELS: Record<EventSource, string> = {
  [EventSource.USER]: 'User',
  [EventSource.SYSTEM]: 'System',
};

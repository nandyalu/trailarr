export interface NotificationChannelRead {
  id: number;
  name: string;
  enabled: boolean;
  event_types: string[]; // EventType NAMES, e.g. 'TRAILER_DOWNLOADED'
  include_user_events: boolean;
  url_masked: string;
  added_at: string;
  updated_at: string;
}

export interface NotificationChannelCreate {
  name: string;
  url: string; // write-only; blank on update = keep existing
  enabled: boolean;
  event_types: string[];
  include_user_events: boolean;
}

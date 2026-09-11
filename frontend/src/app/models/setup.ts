/** The state of the first-run setup guide for this installation. */
export interface SetupStatus {
  /** True while the guide has not been finished or skipped. */
  needed: boolean;
  completed: boolean;
  /** How many connections exist. The guide's first real step. */
  connections: number;
  /** How many media items exist. Zero until the first sync finishes. */
  media: number;
  /** False means preview mode: Trailarr shows what it would download. */
  downloads_enabled: boolean;
  tmdb_key_set: boolean;
}

import {DatePipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, inject} from '@angular/core';
import {RouterLink} from '@angular/router';
import {MediaPendingProfile} from 'src/app/models/pending';
import {videoTypeLabel} from 'src/app/models/trailerprofile';
import {MediaService} from 'src/app/services/media.service';
import {ProfileService} from 'src/app/services/profile.service';

/** Per-profile download matrix (Phase 3): renders GET /media/{id}/pending —
 * which profiles match this item, which are satisfied by which download,
 * which are pending or backing off. Same satisfaction rule as the download
 * task, so this section and the engine can never disagree. */
@Component({
  selector: 'media-pending',
  imports: [DatePipe, RouterLink],
  templateUrl: './pending.component.html',
  styleUrl: './pending.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PendingComponent {
  private readonly mediaService = inject(MediaService);
  private readonly profileService = inject(ProfileService);

  /** The type of video a row is about (Phase 9): the type of the download
   * that satisfies the profile, or else the type the profile downloads. A
   * download or profile with no stored type is a trailer. */
  protected typeLabel(profile: MediaPendingProfile): string {
    const download = profile.satisfied_by
      ? (this.mediaService.selectedMedia()?.downloads ?? []).find((d) => d.id === profile.satisfied_by)
      : undefined;
    if (download) {
      return videoTypeLabel(download.video_type || 'trailer');
    }
    const stored = this.profileService.allProfiles.value().find((p) => p.id === profile.profile_id);
    return videoTypeLabel(stored?.video_type || 'trailer');
  }

  protected readonly pendingView = computed(() => this.mediaService.mediaPendingResource.value());
  protected readonly profiles = computed(() => this.pendingView()?.profiles ?? []);
  protected readonly isMonitored = computed(() => this.pendingView()?.monitor ?? true);

  /** Why an upgrade profile keeps its trailer while TMDB lists nothing for it.
   * Three cases read differently, and the page says which. */
  protected awaitingDetail(): string {
    const view = this.pendingView();
    if (view && !view.has_tmdb_id) {
      return 'TMDB cannot be asked for a better one: this item has no TMDB id';
    }
    if (view && !view.tmdb_asked) {
      return 'Trailarr has not asked TMDB about this item yet; the Refresh Video Lists task will';
    }
    return 'TMDB lists no trailer that the profile can use, so it stays; Trailarr asks TMDB again every 7 days';
  }

  protected stateOf(profile: MediaPendingProfile): 'satisfied' | 'backoff' | 'pending' | 'disabled' | 'not-matching' {
    if (profile.satisfied) return 'satisfied';
    if (profile.backing_off) return 'backoff';
    if (profile.pending) return 'pending';
    if (!profile.enabled) return 'disabled';
    return 'not-matching';
  }

  protected stateLabel(profile: MediaPendingProfile): string {
    switch (this.stateOf(profile)) {
      case 'satisfied':
        return 'Satisfied';
      case 'backoff':
        return 'Backing off';
      case 'pending':
        return 'Pending';
      case 'disabled':
        return 'Disabled';
      case 'not-matching':
        return 'Not matching';
    }
  }

  protected stateDetail(profile: MediaPendingProfile): string {
    switch (this.stateOf(profile)) {
      case 'satisfied': {
        let base: string;
        switch (profile.satisfied_via) {
          case 'own_download':
            base = 'Has its own download';
            break;
          case 'claim':
            base = 'Will claim an existing unassigned download';
            break;
          default:
            base = 'Satisfied by an existing download';
        }
        // With Upgrade To TMDB Trailer on, say what the upgrade makes of
        // the trailer, so nobody wonders why it was not replaced.
        switch (profile.upgrade_state) {
          case 'matched':
            return `${base}, and it is a TMDB trailer or a video you chose`;
          case 'awaiting_tmdb':
            return `${base}. ${this.awaitingDetail()}`;
          case 'unknown_kept':
            return `${base}. Trailarr does not know which video it is, so the TMDB upgrade keeps it; turn on Replace Unknown Videos in the profile to replace it`;
          default:
            return base;
        }
      }
      case 'backoff':
        return `${profile.attempt_count} failed attempt${profile.attempt_count === 1 ? '' : 's'}`;
      case 'pending':
        if (profile.upgrade) {
          const why =
            profile.upgrade_state === 'replace_unknown'
              ? 'Trailarr does not know which video the trailer is'
              : 'the trailer is not a TMDB trailer';
          return this.isMonitored()
            ? `Will replace the trailer with a TMDB trailer on the next run: ${why}`
            : `Would replace the trailer with a TMDB trailer (${why}), but this item is not monitored`;
        }
        return this.isMonitored() ? 'Will download on the next run' : 'Would download, but this item is not monitored';
      case 'disabled':
        return 'Profile is disabled';
      case 'not-matching':
        return "Profile filters don't match this item";
    }
  }
}

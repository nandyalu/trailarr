import {DatePipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, inject} from '@angular/core';
import {RouterLink} from '@angular/router';
import {MediaPendingProfile} from 'src/app/models/pending';
import {MediaService} from 'src/app/services/media.service';

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

  protected readonly pendingView = computed(() => this.mediaService.mediaPendingResource.value());
  protected readonly profiles = computed(() => this.pendingView()?.profiles ?? []);
  protected readonly isMonitored = computed(() => this.pendingView()?.monitor ?? true);

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
      case 'satisfied':
        switch (profile.satisfied_via) {
          case 'own_download':
            return 'Has its own download';
          case 'claim':
            return 'Will claim an existing unassigned download';
          case 'stop_monitoring':
            return "Covered by a stop-monitoring profile's download";
          default:
            return 'Satisfied by an existing download';
        }
      case 'backoff':
        return `${profile.attempt_count} failed attempt${profile.attempt_count === 1 ? '' : 's'}`;
      case 'pending':
        return this.isMonitored() ? 'Will download on the next run' : 'Would download, but this item is not monitored';
      case 'disabled':
        return 'Profile is disabled';
      case 'not-matching':
        return "Profile filters don't match this item";
    }
  }
}

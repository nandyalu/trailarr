import {ChangeDetectionStrategy, Component, computed, inject, input} from '@angular/core';
import {MediaTrailerStatus, TrailerStatusEnum} from '../../../models/mediatrailerstatus';
import {MediaService} from '../../../services/media.service';

interface ProfileGroup {
  profileId: number | null;
  profileName: string;
  videoType: string;
  rows: MediaTrailerStatus[];
}

@Component({
  selector: 'app-trailer-status',
  templateUrl: './trailer-status.component.html',
  styleUrl: './trailer-status.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TrailerStatusComponent {
  readonly statuses = input.required<MediaTrailerStatus[]>();
  readonly isMovie = input<boolean>(false);

  private readonly mediaService = inject(MediaService);

  readonly groups = computed<ProfileGroup[]>(() => {
    const rows = this.statuses();
    const map = new Map<string, ProfileGroup>();
    for (const row of rows) {
      const key = String(row.profile_id ?? 'manual');
      if (!map.has(key)) {
        map.set(key, {
          profileId: row.profile_id,
          profileName: row.profile_name ?? 'Manual / Unattributed',
          videoType: row.video_type ?? 'trailer',
          rows: [],
        });
      }
      map.get(key)!.rows.push(row);
    }
    return Array.from(map.values());
  });

  seasonLabel(season: number): string {
    if (this.isMovie()) return '';
    return season === 0 ? 'Series' : `Season ${season}`;
  }

  statusClass(status: TrailerStatusEnum): string {
    switch (status) {
      case 'downloaded': return 'success';
      case 'downloading': return 'info';
      case 'pending': return 'warning';
      case 'failed': return 'danger';
      case 'skipped':
      case 'unmonitored':
      case 'not_available': return 'muted';
      default: return 'muted';
    }
  }

  statusLabel(status: TrailerStatusEnum): string {
    switch (status) {
      case 'not_available': return 'Not Available';
      default: return status.charAt(0).toUpperCase() + status.slice(1);
    }
  }

  async setUnmonitored(row: MediaTrailerStatus): Promise<void> {
    await this.mediaService.setTrailerStatus(row.id, 'unmonitored' as TrailerStatusEnum).toPromise();
    this.mediaService.mediaTrailerStatusResource.reload();
  }

  async resetPending(row: MediaTrailerStatus): Promise<void> {
    await this.mediaService.setTrailerStatus(row.id, 'pending' as TrailerStatusEnum).toPromise();
    this.mediaService.mediaTrailerStatusResource.reload();
  }
}

import {DatePipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, inject, input} from '@angular/core';
import {RouterLink} from '@angular/router';
import {DurationSecondsConvertPipe} from 'src/app/helpers/duration-seconds-pipe';
import {FileSizePipe} from 'src/app/helpers/file-size.pipe';
import {Download} from 'src/app/models/media';
import {MediaService} from 'src/app/services/media.service';
import {ProfileService} from 'src/app/services/profile.service';
import {WebsocketService} from 'src/app/services/websocket.service';

@Component({
  selector: 'media-downloads',
  imports: [DatePipe, DurationSecondsConvertPipe, FileSizePipe, RouterLink],
  templateUrl: './downloads.component.html',
  styleUrl: './downloads.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DownloadsComponent {
  private readonly profileService = inject(ProfileService);
  private readonly mediaService = inject(MediaService);
  private readonly webSocketService = inject(WebsocketService);

  downloads = input.required<Download[]>();
  hasDownloads = computed(() => this.downloads().length > 0);

  allProfiles = computed(() => this.profileService.allProfiles.value());

  // Map of profile IDs to profile names, used for displaying download profile names in template
  profilesMap = computed(() => {
    const profiles = this.profileService.allProfiles.value();
    const _profileMap = new Map<number, string>();
    profiles.forEach((profile) => {
      _profileMap.set(profile.id, profile.customfilter.filter_name);
    });
    return _profileMap;
  });

  getYouTubeUrl(youtubeId: string): string {
    return `https://www.youtube.com/watch?v=${youtubeId}`;
  }

  /**
   * Opens the assign dropdown above the button when there isn't enough room
   * below it in the viewport. Applied on click (before the popover opens)
   * because CSS position-try-fallbacks doesn't fire for in-flow anchors.
   */
  setDropdownDirection(button: HTMLElement, popover: HTMLElement) {
    const estimatedHeight = 24 + Math.max(1, this.allProfiles().length) * 40;
    const spaceBelow = window.innerHeight - button.getBoundingClientRect().bottom;
    popover.classList.toggle('open-up', spaceBelow < estimatedHeight);
  }

  /**
   * Assigns a trailer profile to a download that has no profile linked
   * (profile_id=0). Success toast arrives via the websocket broadcast;
   * downloads are reloaded so the new profile shows up.
   */
  assignProfile(download: Download, profileId: number, popover: HTMLElement) {
    popover.hidePopover();
    this.mediaService.updateDownloadProfile(download.media_id, download.id, profileId).subscribe({
      next: () => {
        this.mediaService.mediaDownloadsResource.reload();
      },
      error: (error) => {
        this.webSocketService.showToast(error.error?.detail || 'Failed to assign profile!', 'Error');
      },
    });
  }
}

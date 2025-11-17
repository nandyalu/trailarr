import {DatePipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, inject, input} from '@angular/core';
import {RouterLink} from '@angular/router';
import {DurationSecondsConvertPipe} from 'src/app/helpers/duration-seconds-pipe';
import {FileSizePipe} from 'src/app/helpers/file-size.pipe';
import {Download} from 'src/app/models/media';
import {ProfileService} from 'src/app/services/profile.service';

@Component({
  selector: 'media-downloads',
  imports: [DatePipe, DurationSecondsConvertPipe, FileSizePipe, RouterLink],
  templateUrl: './downloads.component.html',
  styleUrl: './downloads.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DownloadsComponent {
  private readonly profileService = inject(ProfileService);

  downloads = input.required<Download[]>();
  hasDownloads = computed(() => this.downloads().length > 0);

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
}

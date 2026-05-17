import {DatePipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, inject} from '@angular/core';
import {DurationConvertPipe} from 'src/app/helpers/duration-pipe';
import {RemoveStartingSlashPipe} from 'src/app/helpers/remove-starting-slash.pipe';
import {ScrollNearEndDirective} from 'src/app/helpers/scroll-near-end-directive';

import {MediaService} from 'src/app/services/media.service';
import {MediaCardShellComponent} from '../media-card-shell/media-card-shell.component';

@Component({
  selector: 'media-expanded-card',
  imports: [DatePipe, DurationConvertPipe, MediaCardShellComponent, RemoveStartingSlashPipe, ScrollNearEndDirective],
  templateUrl: './expanded.component.html',
  styleUrl: './expanded.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ExpandedComponent {
  private readonly mediaService = inject(MediaService);

  protected readonly checkedMediaIDs = this.mediaService.checkedMediaIDs;
  protected readonly defaultDisplayCount = this.mediaService.defaultDisplayCount;
  protected readonly displayCount = this.mediaService.displayCount;
  protected readonly displayMedia = this.mediaService.displayMedia;
  protected readonly filteredSortedMedia = this.mediaService.filteredSortedMedia;
  protected readonly inEditMode = this.mediaService.inEditMode;
  protected readonly selectedMediaID = this.mediaService.selectedMediaID;
  protected readonly expandedFields = this.mediaService.expandedFields;

  protected readonly onMediaChecked = this.mediaService.onMediaChecked.bind(this.mediaService);

  protected hasField(field: string): boolean {
    return this.expandedFields().includes(field);
  }

  protected trailerDownloadedCount(media: any): number {
    return (media.trailer_statuses ?? []).filter(
      (s: any) => s.status === 'downloaded'
    ).length;
  }

  onNearEndScroll(): void {
    if (this.displayCount() >= this.filteredSortedMedia().length) return;
    this.displayCount.update((count) => count + this.defaultDisplayCount);
  }
}

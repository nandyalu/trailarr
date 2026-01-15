import {ChangeDetectionStrategy, Component, inject} from '@angular/core';
import {RouterLink} from '@angular/router';
import {DisplayTitlePipe} from 'src/app/helpers/display-title.pipe';
import {RemoveStartingSlashPipe} from 'src/app/helpers/remove-starting-slash.pipe';
import {ScrollNearEndDirective} from 'src/app/helpers/scroll-near-end-directive';
import {MediaService} from 'src/app/services/media.service';
import {RouteMedia} from 'src/routing';
import {StatusIconComponent} from '../status-icon/status-icon.component';

@Component({
  selector: 'media-poster-card',
  imports: [DisplayTitlePipe, RemoveStartingSlashPipe, RouterLink, ScrollNearEndDirective, StatusIconComponent],
  templateUrl: './poster.component.html',
  styleUrl: './poster.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PosterComponent {
  private readonly mediaService = inject(MediaService);

  // Signals from Media Service
  protected readonly checkedMediaIDs = this.mediaService.checkedMediaIDs;
  protected readonly defaultDisplayCount = this.mediaService.defaultDisplayCount;
  protected readonly displayCount = this.mediaService.displayCount;
  protected readonly displayMedia = this.mediaService.displayMedia;
  protected readonly filteredSortedMedia = this.mediaService.filteredSortedMedia;
  protected readonly inEditMode = this.mediaService.inEditMode;
  protected readonly selectedMediaID = this.mediaService.selectedMediaID;

  // Functions from Media Service
  protected readonly onMediaChecked = this.mediaService.onMediaChecked.bind(this);

  // Constants
  protected readonly RouteMedia = RouteMedia;

  /**
   * Handles the event when the user scrolls near the end of the media list.
   * Loads more media items into the display list if there are more items to show.
   *
   * @returns {void} This method does not return a value.
   */
  onNearEndScroll(): void {
    // Load more media when near the end of the scroll
    if (this.displayCount() >= this.filteredSortedMedia().length) {
      return;
    }
    this.displayCount.update((count) => count + this.defaultDisplayCount);
  }
}

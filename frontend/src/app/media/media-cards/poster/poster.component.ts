import {ChangeDetectionStrategy, Component, inject} from '@angular/core';
import {RemoveStartingSlashPipe} from 'src/app/helpers/remove-starting-slash.pipe';
import {ScrollNearEndDirective} from 'src/app/helpers/scroll-near-end-directive';
import {MediaService} from 'src/app/services/media.service';
import {MediaCardShellComponent} from '../media-card-shell/media-card-shell.component';

@Component({
  selector: 'media-poster-card',
  imports: [MediaCardShellComponent, RemoveStartingSlashPipe, ScrollNearEndDirective],
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

  protected readonly onMediaChecked = this.mediaService.onMediaChecked.bind(this.mediaService);

  onNearEndScroll(): void {
    if (this.displayCount() >= this.filteredSortedMedia().length) return;
    this.displayCount.update((count) => count + this.defaultDisplayCount);
  }
}

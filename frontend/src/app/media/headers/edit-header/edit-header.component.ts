import {ChangeDetectionStrategy, Component, inject, ViewContainerRef} from '@angular/core';
import {MediaService} from 'src/app/services/media.service';
import {WebsocketService} from 'src/app/services/websocket.service';
import {ProfileSelectDialogComponent} from '../../dialogs/profile-select-dialog/profile-select-dialog.component';

@Component({
  selector: 'app-edit-header',
  imports: [],
  templateUrl: './edit-header.component.html',
  styleUrl: './edit-header.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditHeaderComponent {
  protected readonly mediaService = inject(MediaService);
  protected readonly webSocketService = inject(WebsocketService);
  private viewContainerRef = inject(ViewContainerRef);

  // Signals from Media Service
  protected readonly checkedMediaIDs = this.mediaService.checkedMediaIDs;
  protected readonly filteredSortedMedia = this.mediaService.filteredSortedMedia;
  protected readonly inEditMode = this.mediaService.inEditMode;

  selectAll(): void {
    this.checkedMediaIDs.set(this.filteredSortedMedia().map((media) => media.id));
  }

  clearSelection(): void {
    // Clear the selection of media items
    this.checkedMediaIDs.set([]);
  }

  openProfileSelectDialog(): void {
    // Open the dialog for selecting a profile
    const dialogRef = this.viewContainerRef.createComponent(ProfileSelectDialogComponent);
    dialogRef.instance.onSubmit.subscribe((profileId: number) => {
      // Handle the profile selection
      this.batchUpdate('download', profileId); // Perform the batch update action
      setTimeout(() => {
        dialogRef.destroy(); // Destroy the dialog component after use
      }, 3000);
    });
    dialogRef.instance.onClosed.subscribe(() => {
      // Handle dialog close
      setTimeout(() => {
        dialogRef.destroy(); // Destroy the dialog component after use
      }, 3000);
    });
  }

  /**
   * Handles the batch update action for the selected media items.
   *
   * @param {string} action
   * The action to perform on the selected media items. Available actions are:
   * - `monitor`: Monitor the selected media items.
   * - `unmonitor`: Unmonitor the selected media items.
   * - `delete`: Delete the trailers for the selected media items.
   * - `download`: Download the trailers for the selected media items.
   * @param {number} profileID
   * The ID of the profile to use for the download action. \
   * Defaults to `-1` if not provided. \
   * Only required for `download` action.
   * @returns {void}
   */
  batchUpdate(action: string, profileID: number = -1): void {
    this.webSocketService.showToast(`Batch update: ${action} ${this.checkedMediaIDs().length} items`);
    this.mediaService.batchUpdate(this.checkedMediaIDs(), action, profileID).subscribe(() => {
      this.mediaService.mediaResource.reload(); // Fetch updated media items
    });
    this.checkedMediaIDs.set([]);
  }
}

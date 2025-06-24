import {TitleCasePipe} from '@angular/common';
import {Component, computed, effect, ElementRef, inject, input, signal, ViewChild, ViewContainerRef} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {catchError, of} from 'rxjs';
import {CopyToClipboardDirective} from 'src/app/helpers/copy-to-clipboard.directive';
import {ConnectionService} from 'src/app/services/connection.service';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {DurationConvertPipe} from '../../helpers/duration-pipe';
import {MediaService} from '../../services/media.service';
import {WebsocketService} from '../../services/websocket.service';
import {ProfileSelectDialogComponent} from '../dialogs/profile-select-dialog/profile-select-dialog.component';
import {FilesComponent} from './files/files.component';

@Component({
  selector: 'app-media-details',
  imports: [CopyToClipboardDirective, FormsModule, DurationConvertPipe, LoadIndicatorComponent, TitleCasePipe, FilesComponent],
  templateUrl: './media-details.component.html',
  styleUrl: './media-details.component.scss',
})
export class MediaDetailsComponent {
  private readonly mediaService = inject(MediaService);
  private readonly connectionService = inject(ConnectionService);
  private readonly websocketService = inject(WebsocketService);
  private readonly viewContainerRef = inject(ViewContainerRef);

  mediaId = input(0, {transform: Number});
  selectedMedia = this.mediaService.selectedMedia;
  isLoading = computed(() => this.mediaService.mediaResource.isLoading());
  isLoadingMonitor = signal<boolean>(false);
  isLoadingDownload = signal<boolean>(false);
  trailer_url: string = '';
  arr_url = computed(() => {
    let media = this.selectedMedia();
    if (!media) return '';
    let connections = this.connectionService.connectionsResource.value();
    let connection = connections.find((c) => c.id == media.connection_id);
    if (!connection) return '';
    if (connection.arr_type.toLowerCase() == 'radarr') {
      return connection.url + '/movie/' + media.txdb_id;
    } else {
      return connection.url + '/series/' + media.title_slug;
    }
  });

  // Load media data when the media ID changes
  mediaIDChangeEffect = effect(() => {
    this.mediaService.selectedMediaID.set(this.mediaId());
  });

  mediaDataChangeEffect = effect(() => {
    const media = this.selectedMedia();
    if (media) {
      this.trailer_url = media.youtube_trailer_id;
    }
  });

  openProfileSelectDialog(isNextActionSearch: boolean): void {
    // Open the dialog for selecting a profile
    const dialogRef = this.viewContainerRef.createComponent(ProfileSelectDialogComponent);
    dialogRef.instance.onSubmit.subscribe((profileId: number) => {
      // Handle the profile selection
      if (isNextActionSearch) {
        this.searchTrailer(profileId);
      } else {
        this.downloadTrailer(profileId);
      }
      setTimeout(() => {
        dialogRef.destroy(); // Destroy the dialog component after use
      }, 3000);
    });
    dialogRef.instance.onClosed.subscribe(() => {
      // Handle dialog close
      setTimeout(() => {
        dialogRef.destroy(); // Destroy the dialog when closed
      }, 3000);
    });
  }

  /**
   * Downloads the trailer for the current media if the trailer ID has changed.
   *
   * This method checks if the new trailer URL contains the old trailer ID and if the trailer already exists.
   * If the trailer ID is the same and the trailer exists, it does not proceed with the download.
   * Otherwise, it sets the loading state to true and initiates the download process via the media service.
   *
   * @param {number} profileId - The ID of the profile to use for downloading the trailer.
   *
   * @returns {void}
   */
  downloadTrailer(profileId: number): void {
    const old_id = this.selectedMedia()?.youtube_trailer_id?.toLowerCase() || '';
    const new_id = this.trailer_url.toLowerCase();
    if (new_id.includes(old_id) && this.selectedMedia()?.trailer_exists) {
      // Trailer id is the same, no need to download
      return;
    }
    this.isLoadingDownload.set(true);
    // console.log('Downloading trailer');
    this.mediaService.downloadMediaTrailer(this.mediaId(), profileId, this.trailer_url).subscribe((res: string) => {
      console.log(res);
    });
  }

  /**
   * Toggles the monitoring status of the current media item.
   *
   * This method sets the `isLoadingMonitor` flag to true, then toggles the `monitor` status of the media item.
   * It calls the `monitorMedia` method of `mediaService` with the media ID and the new monitor status.
   * Once the subscription receives a response, it logs the response, updates the media's monitor status,
   * and sets the `isLoadingMonitor` flag to false.
   */
  monitorMedia() {
    // console.log('Toggling Media Monitoring');
    this.isLoadingMonitor.set(true);
    const monitor = !this.selectedMedia()?.monitor;
    this.mediaService.monitorMedia(this.mediaId(), monitor).subscribe((res: string) => {
      console.log(res);
      this.selectedMedia()!.monitor = monitor;
      this.isLoadingMonitor.set(false);
    });
  }

  searchTrailer(profileID: number) {
    // console.log('Searching for trailer');
    this.websocketService.showToast('Searching for trailer...');
    this.isLoadingDownload.set(true);
    this.mediaService
      .searchMediaTrailer(this.mediaId(), profileID)
      .pipe(
        catchError((error) => {
          console.error('Error searching trailer:', error.error.detail);
          this.websocketService.showToast(error.error.detail, 'Error');
          this.isLoadingDownload.set(false);
          return of('');
        }),
      )
      .subscribe((res: string) => {
        if (res) {
          this.selectedMedia()!.youtube_trailer_id = res;
          this.trailer_url = res;
        }
        this.isLoadingDownload.set(false);
      });
  }

  saveYtId() {
    // console.log('Saving youtube id');
    this.websocketService.showToast('Saving youtube id...');
    this.isLoadingDownload.set(true);
    this.mediaService
      .saveMediaTrailer(this.mediaId(), this.trailer_url)
      .pipe(
        catchError((error) => {
          console.error('Error searching trailer:', error.error.detail);
          this.websocketService.showToast(error.error.detail, 'Error');
          this.isLoadingDownload.set(false);
          return of('');
        }),
      )
      .subscribe((res: string) => {
        if (res) {
          this.selectedMedia()!.youtube_trailer_id = res;
          this.trailer_url = res;
        }
        this.isLoadingDownload.set(false);
      });
  }

  /**
   * Opens a new browser tab to play the YouTube trailer of the current media.
   * If the media does not have a YouTube trailer ID, the function returns without doing anything.
   *
   * @returns {void}
   */
  openTrailer(): void {
    if (!this.selectedMedia()?.youtube_trailer_id) {
      return;
    }
    window.open(`https://www.youtube.com/watch?v=${this.selectedMedia()?.youtube_trailer_id}`, '_blank');
  }

  // Reference to the dialog element
  @ViewChild('deleteDialog') deleteDialog!: ElementRef<HTMLDialogElement>;

  /**
   * Displays the delete dialog modal.
   * This method opens the delete dialog by calling the `showModal` method
   * on the native element of the delete dialog.
   *
   * @returns {void}
   */
  showDeleteDialog(): void {
    this.deleteDialog.nativeElement.showModal(); // Open the dialog
  }

  /**
   * Closes the delete dialog.
   *
   * This method is used to close the delete dialog by accessing the native element
   * and invoking the `close` method on it.
   */
  closeDeleteDialog(): void {
    this.deleteDialog.nativeElement.close(); // Close the dialog
  }

  /**
   * Handles the confirmation of trailer deletion.
   * Closes the delete dialog and calls the media service to delete the trailer.
   * Updates the media object to reflect that the trailer no longer exists.
   */
  onConfirmDelete() {
    // console.log('Deleting trailer');
    this.closeDeleteDialog();
    this.mediaService.deleteMediaTrailer(this.mediaId()).subscribe((res: string) => {
      console.log(res);
      this.selectedMedia()!.trailer_exists = false;
    });
  }
}

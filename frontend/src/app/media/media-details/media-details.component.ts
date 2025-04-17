import {NgIf, TitleCasePipe} from '@angular/common';
import {Component, effect, ElementRef, input, ViewChild} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {ActivatedRoute} from '@angular/router';
import {catchError, of, Subscription} from 'rxjs';
import {DurationConvertPipe} from '../../helpers/duration-pipe';
import {Media} from '../../models/media';
import {MediaService} from '../../services/media.service';
import {WebsocketService} from '../../services/websocket.service';
import {FilesComponent} from './files/files.component';

@Component({
  selector: 'app-media-details',
  imports: [NgIf, FormsModule, DurationConvertPipe, TitleCasePipe, FilesComponent],
  templateUrl: './media-details.component.html',
  styleUrl: './media-details.component.css',
})
export class MediaDetailsComponent {
  mediaId = input(0, {transform: Number});
  media?: Media = undefined;
  isLoading = true;
  isLoadingMonitor = false;
  isLoadingDownload = false;
  trailer_url: string = '';
  private webSocketSubscription?: Subscription;

  constructor(
    private mediaService: MediaService,
    private route: ActivatedRoute,
    private websocketService: WebsocketService,
  ) {}

  /**
   * Copies the provided text to the clipboard. If the Clipboard API is not available,
   * it falls back to using the `execCommand` method for wider browser compatibility.
   *
   * @param textToCopy - The text string to be copied to the clipboard.
   * @returns A promise that resolves when the text has been successfully copied.
   *
   * @remarks
   * This method uses the modern Clipboard API if available, and falls back to the
   * `execCommand` method for older browsers. It also displays a toast notification
   * indicating the success or failure of the copy operation.
   *
   * @example
   * ```typescript
   * this.copyToClipboard("Hello, World!");
   * ```
   */
  async copyToClipboard(textToCopy: string) {
    if (!navigator.clipboard) {
      // Fallback to the old execCommand() way (for wider browser coverage)
      const tempInput = document.createElement('input');
      tempInput.value = textToCopy;
      document.body.appendChild(tempInput);
      tempInput.select();
      document.execCommand('copy');
      document.body.removeChild(tempInput);
      this.websocketService.showToast('Copied to clipboard!');
    } else {
      try {
        await navigator.clipboard.writeText(textToCopy);
        this.websocketService.showToast('Copied to clipboard!');
      } catch (err) {
        this.websocketService.showToast('Error copying text to clipboard.', 'Error');
        console.error('Failed to copy: ', err);
      }
    }
    return;
  }

  // Load media data when the media ID changes
  mediaEffect = effect(() => {
    this.isLoading = true;
    this.getMediaData();
  });

  ngOnInit(): void {
    this.isLoading = true;
    // this.route.params.subscribe(params => {
    //   this.mediaId.set(parseInt(params['id']));
    //   this.getMediaData();
    // });

    // Subscribe to WebSocket updates and refresh media data
    this.webSocketSubscription = this.websocketService.toastMessage.subscribe(() => {
      this.getMediaData();
    });
  }

  ngOnDestroy() {
    // Unsubscribe from the websocket events
    this.webSocketSubscription?.unsubscribe();
  }

  /**
   * Fetches media data based on the current media ID. \
   * Also sets the `trailer_url` property to the YouTube trailer ID of the media.
   * @returns {void}
   */
  getMediaData(): void {
    // Get Media Data
    this.mediaService.getMediaByID(this.mediaId()).subscribe((media_res: Media) => {
      this.media = media_res;
      this.trailer_url = media_res.youtube_trailer_id;
      this.isLoading = false;
    });
  }

  /**
   * Downloads the trailer for the current media if the trailer ID has changed.
   *
   * This method checks if the new trailer URL contains the old trailer ID and if the trailer already exists.
   * If the trailer ID is the same and the trailer exists, it does not proceed with the download.
   * Otherwise, it sets the loading state to true and initiates the download process via the media service.
   *
   * @returns {void}
   */
  downloadTrailer() {
    const old_id = this.media?.youtube_trailer_id?.toLowerCase() || '';
    const new_id = this.trailer_url.toLowerCase();
    if (new_id.includes(old_id) && this.media?.trailer_exists) {
      // Trailer id is the same, no need to download
      return;
    }
    this.isLoadingDownload = true;
    // console.log('Downloading trailer');
    this.mediaService.downloadMediaTrailer(this.mediaId(), this.trailer_url).subscribe((res: string) => {
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
  monitorSeries() {
    // console.log('Toggling Media Monitoring');
    this.isLoadingMonitor = true;
    const monitor = !this.media?.monitor;
    this.mediaService.monitorMedia(this.mediaId(), monitor).subscribe((res: string) => {
      console.log(res);
      this.media!.monitor = monitor;
      this.isLoadingMonitor = false;
    });
  }

  searchTrailer() {
    // console.log('Searching for trailer');
    this.websocketService.showToast('Searching for trailer...');
    this.isLoadingDownload = true;
    this.mediaService
      .searchMediaTrailer(this.mediaId())
      .pipe(
        catchError((error) => {
          console.error('Error searching trailer:', error.error.detail);
          this.websocketService.showToast(error.error.detail, 'Error');
          this.isLoadingDownload = false;
          return of('');
        }),
      )
      .subscribe((res: string) => {
        if (res) {
          this.media!.youtube_trailer_id = res;
          this.trailer_url = res;
        }
        this.isLoadingDownload = false;
      });
  }

  saveYtId() {
    // console.log('Saving youtube id');
    this.websocketService.showToast('Saving youtube id...');
    this.isLoadingDownload = true;
    this.mediaService
      .saveMediaTrailer(this.mediaId(), this.trailer_url)
      .pipe(
        catchError((error) => {
          console.error('Error searching trailer:', error.error.detail);
          this.websocketService.showToast(error.error.detail, 'Error');
          this.isLoadingDownload = false;
          return of('');
        }),
      )
      .subscribe((res: string) => {
        if (res) {
          this.media!.youtube_trailer_id = res;
          this.trailer_url = res;
        }
        this.isLoadingDownload = false;
      });
  }

  /**
   * Opens a new browser tab to play the YouTube trailer of the current media.
   * If the media does not have a YouTube trailer ID, the function returns without doing anything.
   *
   * @returns {void}
   */
  openTrailer(): void {
    if (!this.media?.youtube_trailer_id) {
      return;
    }
    window.open(`https://www.youtube.com/watch?v=${this.media.youtube_trailer_id}`, '_blank');
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
      this.media!.trailer_exists = false;
    });
  }
}

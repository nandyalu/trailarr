import { NgFor, NgIf, NgTemplateOutlet, TitleCasePipe } from '@angular/common';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs';
import { DurationConvertPipe } from '../../helpers/duration-pipe';
import { FolderInfo, Media } from '../../models/media';
import { MediaService } from '../../services/media.service';
import { WebsocketService } from '../../services/websocket.service';

@Component({
  selector: 'app-media-details',
  standalone: true,
  imports: [NgIf, NgFor, FormsModule, DurationConvertPipe, NgTemplateOutlet, TitleCasePipe],
  templateUrl: './media-details.component.html',
  styleUrl: './media-details.component.css'
})
export class MediaDetailsComponent {
  mediaId: number = 0;
  media?: Media = undefined;
  mediaFiles?: FolderInfo = undefined;
  mediaFilesResponse: string = 'No files found';
  isLoading = true;
  isLoadingMonitor = false;
  isLoadingDownload = false;
  filesLoading = true;
  trailer_url: string = '';
  // status = 'Missing';
  // private mediaService: MovieService | SeriesService = this.seriesService;
  private webSocketSubscription?: Subscription;

  constructor(
    private mediaService: MediaService,
    private route: ActivatedRoute,
    private websocketService: WebsocketService
  ) { }

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
      const tempInput = document.createElement("input");
      tempInput.value = textToCopy;
      document.body.appendChild(tempInput);
      tempInput.select();
      document.execCommand("copy");
      document.body.removeChild(tempInput);
      this.websocketService.showToast("Copied to clipboard!");
    } else {
      try {
        await navigator.clipboard.writeText(textToCopy);
        this.websocketService.showToast("Copied to clipboard!");
      } catch (err) {
        this.websocketService.showToast("Error copying text to clipboard.", "Error");
        console.error('Failed to copy: ', err);
      }
    }
    return;
  }

  ngOnInit(): void {
    this.isLoading = true;
    this.filesLoading = true;
    this.route.params.subscribe(params => {
      // let type = this.route.snapshot.url[0].path;
      // if (type === 'movies') {
      //   this.moviesOnly = true;
      // } else {
      //   this.moviesOnly = false;
      // }
      this.mediaId = params['id'];
      this.getMediaData();
    });

    // Subscribe to the WebSocket events and refresh data
    // Calling this.getMediaData() directly in subscription fails, so we use a handler
    const handleWebSocketEvent = () => {
      this.getMediaData();
    };

    // Subscribe to the WebSocket events with the simplified handler
    this.webSocketSubscription = this.websocketService.connect().subscribe({
      next: handleWebSocketEvent,
      error: handleWebSocketEvent,
      complete: handleWebSocketEvent
    });
    // Subscribe to websocket events to refresh data

  }

  ngOnDestroy() {
    // Unsubscribe from the websocket events
    this.webSocketSubscription?.unsubscribe();
  }

  /**
   * Fetches media data and media files based on the current media ID.
   * 
   * This method performs two asynchronous operations:
   * 1. Retrieves media data from the media service and assigns it to the `media` property.
   *    - Sets the `trailer_url` property using the `youtube_trailer_id` from the media response.
   *    - Sets the `isLoading` flag to `false` once the media data is retrieved.
   * 2. Retrieves media files from the media service and assigns them to the `mediaFiles` property.
   *    - If the response is a string, assigns it to the `mediaFilesResponse` property.
   *    - Sets the `filesLoading` flag to `false` once the media files are retrieved.
   */
  getMediaData() {
    // Get Media Data
    this.mediaService.getMediaById(this.mediaId).subscribe((media_res: Media) => {
      this.media = media_res;
      this.trailer_url = media_res.youtube_trailer_id
      this.isLoading = false;
    });
    // Get Media Files
    this.mediaService.getMediaFiles(this.mediaId).subscribe((files: FolderInfo | string) => {
      if (typeof files === 'string') {
        this.mediaFilesResponse = files;
      } else {
        this.mediaFiles = files;
      }
      this.filesLoading = false;
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
    this.mediaService.downloadMediaTrailer(this.mediaId, this.trailer_url).subscribe((res: string) => {
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
    this.mediaService.monitorMedia(this.mediaId, monitor).subscribe((res: string) => {
      console.log(res);
      this.media!.monitor = monitor;
      this.isLoadingMonitor = false;
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
    this.mediaService.deleteMediaTrailer(this.mediaId).subscribe((res: string) => {
      console.log(res);
      this.media!.trailer_exists = false;
    });
  }
}

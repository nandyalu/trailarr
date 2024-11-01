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

  openTrailer(): void {
    if (!this.media?.youtube_trailer_id) {
      return;
    }
    window.open(`https://www.youtube.com/watch?v=${this.media.youtube_trailer_id}`, '_blank');
  }

  // Reference to the dialog element
  @ViewChild('deleteDialog') deleteDialog!: ElementRef<HTMLDialogElement>;

  showDeleteDialog(): void {
    this.deleteDialog.nativeElement.showModal(); // Open the dialog
  }

  closeDeleteDialog(): void {
    this.deleteDialog.nativeElement.close(); // Close the dialog
  }

  onConfirmDelete() {
    // console.log('Deleting trailer');
    this.closeDeleteDialog();
    this.mediaService.deleteMediaTrailer(this.mediaId).subscribe((res: string) => {
      console.log(res);
      this.media!.trailer_exists = false;
    });
  }
}

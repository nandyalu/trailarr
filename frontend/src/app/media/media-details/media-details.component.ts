import {TitleCasePipe} from '@angular/common';
import {Component, computed, effect, ElementRef, HostListener, inject, input, signal, ViewChild, ViewContainerRef} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Router, RouterLink} from '@angular/router';
import {catchError, of} from 'rxjs';
import {CopyToClipboardDirective} from 'src/app/helpers/copy-to-clipboard.directive';
import {ConnectionService} from 'src/app/services/connection.service';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {RouteMedia} from 'src/routing';
import {DurationConvertPipe} from '../../helpers/duration-pipe';
import {MediaService} from '../../services/media.service';
import {WebsocketService} from '../../services/websocket.service';
import {ProfileSelectDialogComponent} from '../dialogs/profile-select-dialog/profile-select-dialog.component';
import {DownloadsComponent} from './downloads/downloads.component';
import {FilesComponent} from './files/files.component';

@Component({
  selector: 'app-media-details',
  imports: [
    CopyToClipboardDirective,
    DownloadsComponent,
    DurationConvertPipe,
    FilesComponent,
    FormsModule,
    LoadIndicatorComponent,
    RouterLink,
    TitleCasePipe,
  ],
  templateUrl: './media-details.component.html',
  styleUrl: './media-details.component.scss',
})
export class MediaDetailsComponent {
  private readonly mediaService = inject(MediaService);
  private readonly connectionService = inject(ConnectionService);
  private readonly webSocketService = inject(WebsocketService);
  private readonly viewContainerRef = inject(ViewContainerRef);
  private readonly router = inject(Router);

  RouteMedia = RouteMedia;

  mediaId = input(0, {transform: Number});
  selectedMedia = this.mediaService.selectedMedia;
  previousMedia = this.mediaService.previousMedia;
  nextMedia = this.mediaService.nextMedia;
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
    let baseUrl = connection.external_url && connection.external_url.length > 0 ? connection.external_url : connection.url;
    if (baseUrl.endsWith('/')) {
      baseUrl = baseUrl.slice(0, -1);
    }
    if (connection.arr_type.toLowerCase() == 'radarr') {
      return baseUrl + '/movie/' + media.txdb_id;
    } else {
      return baseUrl + '/series/' + media.title_slug;
    }
  });

  // Load media data when the media ID changes
  mediaIDChangeEffect = effect(() => {
    this.mediaService.selectedMediaID.set(this.mediaId());
  });

  mediaDataChangeEffect = effect(() => {
    const media = this.selectedMedia();
    if (media) {
      this.trailer_url = media.youtube_trailer_id || '';
      if (media.status !== 'downloading') {
        this.isLoadingDownload.set(false);
      }
    }
  });

  // Add Hostlisteners to handle keyboard shortcuts
  @HostListener('document:keydown', ['$event'])
  handleKeyboardEvent(event: KeyboardEvent) {
    // Check if the active element is an input, textarea, or contenteditable element
    const activeElement = document.activeElement as HTMLElement;
    const isInputField = activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.isContentEditable;
    // Skip if Ctrl, Alt, or Meta key is pressed
    if (event.ctrlKey || event.altKey || event.metaKey) {
      return;
    }
    // Check if the event is a keydown event and the media ID is set
    if (!isInputField && event.type === 'keydown' && this.mediaId()) {
      // Check if the 'ArrowRight' key is pressed
      if (event.key === 'ArrowRight' || event.key.toLowerCase() === 'n') {
        // If the 'ArrowRight' key is pressed, open Next Media
        let nextMedia1 = this.nextMedia();
        if (nextMedia1) {
          // If there is no next media, navigate to the first media in the list
          this.router.navigate([RouteMedia, nextMedia1.id]);
        }
      }
      // Check if the 'ArrowLeft' key is pressed
      else if (event.key === 'ArrowLeft' || event.key.toLowerCase() === 'p') {
        // If the 'ArrowLeft' key is pressed, open Previous Media
        let previousMedia1 = this.previousMedia();
        if (previousMedia1) {
          // If there is no previous media, navigate to the last media in the list
          this.router.navigate([RouteMedia, previousMedia1.id]);
        }
      }
      // Check if the 'Delete' key is pressed
      else if (event.key === 'Delete' || event.key === 'Backspace') {
        // If the 'Delete' key is pressed, show the delete dialog
        this.showDeleteDialog();
      }
    }
  }

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
    const trailer_exists = this.selectedMedia()?.trailer_exists || false;
    if (old_id && new_id.includes(old_id) && trailer_exists) {
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
    this.webSocketService.showToast('Searching for trailer...');
    this.isLoadingDownload.set(true);
    this.mediaService
      .searchMediaTrailer(this.mediaId(), profileID)
      .pipe(
        catchError((error) => {
          console.error('Error searching trailer:', error.error.detail);
          this.webSocketService.showToast(error.error.detail, 'Error');
          this.isLoadingDownload.set(false);
          return of('');
        }),
      )
      .subscribe(() => {
        this.isLoadingDownload.set(false);
      });
  }

  saveYtId() {
    // console.log('Saving youtube id');
    this.webSocketService.showToast('Saving youtube id...');
    this.isLoadingDownload.set(true);
    this.mediaService
      .saveMediaTrailer(this.mediaId(), this.trailer_url)
      .pipe(
        catchError((error) => {
          console.error('Error searching trailer:', error.error.detail);
          this.webSocketService.showToast(error.error.detail, 'Error');
          this.isLoadingDownload.set(false);
          return of('');
        }),
      )
      .subscribe(() => {
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

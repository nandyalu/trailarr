import {TitleCasePipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, effect, inject, input, signal, ViewContainerRef} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Router, RouterLink} from '@angular/router';
import {catchError, of} from 'rxjs';
import {CopyToClipboardDirective} from 'src/app/shared/directives/copy-to-clipboard.directive';
import {RemoveStartingSlashPipe} from 'src/app/shared/pipes/remove-starting-slash.pipe';
import {ConnectionService} from 'src/app/services/connection.service';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {MediaVideo} from 'src/app/models/media';
import {DEFAULT_VIDEO_TYPE, TrailerProfileRead, VIDEO_TYPE_OPTIONS, VIDEO_TYPES, videoTypeLabel} from 'src/app/models/trailerprofile';
import {ProfileService} from 'src/app/services/profile.service';
import {RouteMedia} from 'src/routing';
import {DurationConvertPipe} from '../../shared/pipes/duration-pipe';
import {MediaService} from '../../services/media.service';
import {WebsocketService} from '../../services/websocket.service';
import {ProfileSelectDialogComponent} from '../dialogs/profile-select-dialog/profile-select-dialog.component';
import {DownloadsComponent} from './downloads/downloads.component';
import {FilesComponent} from './files/files.component';
import {MediaEventsComponent} from './media-events/media-events.component';
import {PendingComponent} from './pending/pending.component';

/** The known videos of one type, in the order the server sent them. */
export interface VideoGroup {
  type: string;
  label: string;
  videos: MediaVideo[];
}

/** The stored type of a video, read defensively: an empty or unknown value
 * is a trailer, as the backend's `normalize_video_type` reads it. */
export function normalizeVideoType(value: string | null | undefined): string {
  const normalized = (value ?? '').trim().toLowerCase();
  return VIDEO_TYPES.includes(normalized) ? normalized : DEFAULT_VIDEO_TYPE;
}

/** Groups videos by type: Trailer first, then the other types in the order
 * of the enum. Inside a group the server order stays — it is the order the
 * resolver tries them. TMDB lists featurettes before trailers for some
 * titles, so an ungrouped list hid the trailer. */
export function groupVideosByType(videos: MediaVideo[]): VideoGroup[] {
  const groups = new Map<string, MediaVideo[]>();
  for (const video of videos) {
    const type = normalizeVideoType(video.video_type);
    if (!groups.has(type)) {
      groups.set(type, []);
    }
    groups.get(type)!.push(video);
  }
  return VIDEO_TYPES.filter((type) => groups.has(type)).map((type) => ({
    type,
    label: videoTypeLabel(type),
    videos: groups.get(type)!,
  }));
}

@Component({
  selector: 'app-media-details',
  imports: [
    CopyToClipboardDirective,
    DownloadsComponent,
    DurationConvertPipe,
    FilesComponent,
    FormsModule,
    LoadIndicatorComponent,
    MediaEventsComponent,
    PendingComponent,
    RemoveStartingSlashPipe,
    RouterLink,
    TitleCasePipe,
  ],
  templateUrl: './media-details.component.html',
  styleUrl: './media-details.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    '(document:keydown)': 'handleKeyboardEvent($event)',
  },
})
export class MediaDetailsComponent {
  private readonly mediaService = inject(MediaService);
  private readonly connectionService = inject(ConnectionService);
  private readonly profileService = inject(ProfileService);
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
    const arrType = connection.arr_type.toLowerCase();
    if (arrType == 'radarr') {
      return baseUrl + '/movie/' + media.txdb_id;
    } else if (arrType == 'sonarr') {
      return baseUrl + '/series/' + media.title_slug;
    }
    return '';
  });

  plex_url = computed(() => {
    const media = this.selectedMedia();
    if (!media?.plex_rating_key || !media?.plex_connection_id) return '';
    const connections = this.connectionService.connectionsResource.value();
    const connection = connections.find((c) => c.id === media.plex_connection_id);
    if (!connection?.machine_identifier) return '';
    const baseUrl = (connection.external_url?.length > 0 ? connection.external_url : connection.url).replace(/\/$/, '');
    return `${baseUrl}/web/index.html#!/server/${connection.machine_identifier}/details?key=%2Flibrary%2Fmetadata%2F${media.plex_rating_key}`;
  });

  // Load media data when the media ID changes
  mediaIDChangeEffect = effect(() => {
    const mediaId = this.mediaId();
    this.mediaService.selectedMediaID.set(mediaId);
    // Read the known videos here rather than with the media data: the
    // media object changes on every websocket update, and during a
    // download that is often. Reading them there sent a request each time.
    this.loadKnownVideos();
  });

  /** Every video Trailarr knows for this item, in the order it would use
   * them. The first one is what a trailer download takes right now. */
  readonly knownVideos = signal<MediaVideo[]>([]);

  /** The known videos by type, Trailer first. */
  readonly videoGroups = computed(() => groupVideosByType(this.knownVideos()));

  /** The video the Watch button opens: the first one in resolver order,
   * which is what a download takes. Phase 9 dropped the stored YouTube id,
   * so the list is the only record. */
  readonly firstVideo = computed<MediaVideo | null>(() => this.knownVideos()[0] ?? null);

  /** The 7 types a video can be, for the add form. */
  readonly videoTypeOptions = VIDEO_TYPE_OPTIONS;

  /** What the user typed into the add form: a YouTube id or URL. */
  newVideoUrl = '';

  /** The language of the video being added, as a 2-letter code. Empty
   * means the video suits a profile that takes any language. */
  videoLanguage = '';

  /** The type of the video being added. */
  newVideoType: string = DEFAULT_VIDEO_TYPE;

  mediaDataChangeEffect = effect(() => {
    const media = this.selectedMedia();
    if (media) {
      this.isLoadingDownload.set(media.status === 'downloading');
    }
  });

  handleKeyboardEvent(event: KeyboardEvent) {
    // Check if the active element is an input, textarea, or contenteditable element
    const activeElement = document.activeElement as HTMLElement;
    const isInputField =
      activeElement.tagName === 'INPUT' ||
      activeElement.tagName === 'TEXTAREA' ||
      activeElement.tagName === 'SELECT' ||
      activeElement.isContentEditable;
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
   * Downloads a video for the current media with a profile.
   *
   * Without a video id the backend picks the video: the first known video
   * of the profile's type, or a YouTube search for a trailer profile. With
   * one, it downloads that video.
   *
   * @param {number} profileId - The ID of the profile to use.
   * @param {string} videoId - The YouTube id to download, or empty.
   */
  downloadTrailer(profileId: number, videoId: string = ''): void {
    this.isLoadingDownload.set(true);
    this.mediaService
      .downloadMediaTrailer(this.mediaId(), profileId, videoId)
      .pipe(
        catchError((error) => {
          this.webSocketService.showToast(error.error?.detail || 'Could not start the download.', 'Error');
          this.isLoadingDownload.set(false);
          return of('');
        }),
      )
      .subscribe((res: string) => {
        if (res) {
          console.log(res);
        }
      });
  }

  /** The profiles that download the given type of video. A profile with no
   * stored type is a trailer profile. */
  profilesForType(videoType: string | null | undefined): TrailerProfileRead[] {
    const wanted = normalizeVideoType(videoType);
    return this.profileService.allProfiles.value().filter((profile) => normalizeVideoType(profile.video_type) === wanted);
  }

  /** Downloads one known video with the chosen profile. */
  downloadKnownVideo(video: MediaVideo, profileId: number, popover: HTMLElement) {
    popover.hidePopover();
    this.webSocketService.showToast(`Downloading ${video.name || video.video_id}...`);
    this.downloadTrailer(profileId, video.video_id);
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
        this.loadKnownVideos();
      });
  }

  /** Adds the video in the add form as one the user chose, with its
   * language and type. */
  addChosenVideo() {
    const url = this.newVideoUrl.trim();
    if (!url) {
      return;
    }
    this.webSocketService.showToast('Saving your video...');
    this.isLoadingDownload.set(true);
    this.mediaService
      .addMediaVideo(this.mediaId(), url, this.videoLanguage.trim(), this.newVideoType)
      .pipe(
        catchError((error) => {
          this.webSocketService.showToast(error.error?.detail || 'Could not add the video.', 'Error');
          this.isLoadingDownload.set(false);
          return of(null);
        }),
      )
      .subscribe((row) => {
        this.isLoadingDownload.set(false);
        if (row) {
          this.newVideoUrl = '';
          this.videoLanguage = '';
          this.newVideoType = DEFAULT_VIDEO_TYPE;
          this.loadKnownVideos();
        }
      });
  }

  /** Reads the known videos for the media item that is open. */
  loadKnownVideos() {
    const mediaId = this.mediaId();
    if (!mediaId) {
      return;
    }
    this.mediaService
      .getMediaVideos(mediaId)
      .pipe(
        catchError(() => {
          // The list is extra information, so a failure to read it must
          // not take over the page.
          return of([] as MediaVideo[]);
        }),
      )
      .subscribe((videos) => this.knownVideos.set(videos));
  }

  /** Removes one known video. A video you chose comes back only if you add
   * it again; a video from TMDB comes back with the next refresh. */
  removeKnownVideo(videoId: string) {
    this.mediaService
      .deleteMediaVideo(this.mediaId(), videoId)
      .pipe(
        catchError((error) => {
          this.webSocketService.showToast(error.error?.detail || 'Could not remove the video.', 'Error');
          return of(null);
        }),
      )
      .subscribe((result) => {
        if (result !== null) {
          this.webSocketService.showToast('Trailarr removed the video.');
          this.loadKnownVideos();
        }
      });
  }

  /** How a source reads on the page. */
  sourceLabel(source: MediaVideo['source']): string {
    switch (source) {
      case 'user':
        return 'You chose this';
      case 'tmdb':
        return 'TMDB';
      case 'arr':
        return 'Radarr / Sonarr';
      case 'search':
        return 'YouTube search';
      default:
        return source;
    }
  }

  /** How a type reads on the page. */
  typeLabel(videoType: string | null | undefined): string {
    return videoTypeLabel(normalizeVideoType(videoType));
  }

  youtubeLink(videoId: string): string {
    return `https://www.youtube.com/watch?v=${videoId}`;
  }

  /**
   * Opens a new browser tab to play the first known video: the one a
   * download would take. Does nothing when Trailarr knows no video.
   *
   * @returns {void}
   */
  openTrailer(): void {
    const video = this.firstVideo();
    if (!video) {
      return;
    }
    window.open(this.youtubeLink(video.video_id), '_blank');
  }
}

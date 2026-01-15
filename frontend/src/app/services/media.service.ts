import {HttpClient, HttpParams, httpResource} from '@angular/common/http';
import {computed, inject, Injectable, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {firstValueFrom, Observable} from 'rxjs';
import {environment} from '../../environment';
import {applySelectedFilter, applySelectedSort} from '../media/utils/apply-filters';
import {buildMediaTreeMap, FileFolderInfo, mapFileFolderInfo} from '../models/filefolderinfo';
import {buildDownloadMap, Download, FolderInfo, mapDownload, mapFolderInfo, mapMedia, Media, SearchMedia} from '../models/media';
import {CustomfilterService} from './customfilter.service';
import {WebsocketService} from './websocket.service';

@Injectable({
  providedIn: 'root',
})
export class MediaService {
  private readonly httpClient = inject(HttpClient);
  private readonly customfilterService = inject(CustomfilterService);
  private readonly webSocketService = inject(WebsocketService);

  private mediaUrl = environment.apiUrl + environment.media;
  private filesUrl = environment.apiUrl + environment.files;

  // Signals from others
  readonly customFilters = this.customfilterService.viewFilters;

  // Constants
  readonly defaultDisplayCount = 50;

  // Signals
  readonly checkedMediaIDs = signal<number[]>([]);
  readonly displayCount = signal<number>(this.defaultDisplayCount);
  readonly inEditMode = signal<boolean>(false);
  readonly moviesOnly = signal<boolean | null>(null);
  readonly selectedMediaID = signal<number | null>(null);
  readonly selectedSort = signal<keyof Media>('added_at');
  readonly sortAscending = signal<boolean>(true);
  readonly selectedFilter = signal<string>('all');

  // Resources
  readonly mediaResource = httpResource<Media[]>(() => ({url: this.mediaUrl + 'all_raw'}), {
    defaultValue: [],
    parse: (response) => {
      if (response && Array.isArray(response)) {
        return response.map(mapMedia);
      }
      return [];
    },
  });
  readonly mediaDownloadsResource = httpResource<Map<number, Download[]>>(() => ({url: this.mediaUrl + 'downloads_raw'}), {
    defaultValue: new Map<number, Download[]>(),
    parse: (response) => {
      if (response && Array.isArray(response)) {
        return buildDownloadMap(response.map(mapDownload));
      }
      return new Map<number, Download[]>();
    },
  });
  readonly mediaFilesResource = httpResource<Map<number, FileFolderInfo>>(() => ({url: this.filesUrl + 'files_raw'}), {
    defaultValue: new Map<number, FileFolderInfo>(),
    parse: (response) => {
      if (response && Array.isArray(response)) {
        return buildMediaTreeMap(response.map(mapFileFolderInfo));
      }
      return new Map<number, FileFolderInfo>();
    },
  });

  // Computed Signals
  /** Combined media list with associated files and downloads */
  readonly combinedMedia = computed<Media[]>(() => {
    const mediaList = this.mediaResource.value();
    const downloadsMap = this.mediaDownloadsResource.value();
    const filesMap = this.mediaFilesResource.value();
    return mediaList.map((media) => {
      const downloads = downloadsMap.get(media.id) || [];
      const files = filesMap.get(media.id) || null;
      return {
        ...media,
        files: files,
        downloads: downloads,
      };
    });
  });

  /** Filtered and sorted media list based on the current filters and sort options
   *
   * @reacts  to changes in:
   * - combinedMedia
   * - moviesOnly
   * - selectedFilter
   * - selectedSort
   * - sortAscending
   *
   * @use  this is the main media list to display in the UI
   */
  readonly filteredSortedMedia = computed(() => {
    // Apply the moviesOnly filter
    let _moviesOnly = this.moviesOnly();
    let moviesOnlyMediaList: Media[];
    switch (_moviesOnly) {
      case true: {
        moviesOnlyMediaList = this.combinedMedia().filter((media) => media.is_movie);
        break;
      }
      case false: {
        moviesOnlyMediaList = this.combinedMedia().filter((media) => !media.is_movie);
        break;
      }
      case null: {
        moviesOnlyMediaList = this.combinedMedia().filter((media) => {
          return media.downloads.some((download) => download.file_exists === true);
        });
        break;
      }
    }
    // Filter the media list by the selected filter option
    let mediaList = applySelectedFilter(moviesOnlyMediaList, this.selectedFilter(), this.customFilters());
    // Sort the media list by the selected sort option
    // Sorts the list in place. If sortAscending is false, reverses the list
    applySelectedSort(mediaList, this.selectedSort(), this.sortAscending());
    return mediaList;
  });

  /** Media list to display based on the current display count */
  readonly displayMedia = computed(() => this.filteredSortedMedia().slice(0, this.displayCount()));

  /** Currently selected media item based on the selectedMediaID */
  readonly selectedMedia = computed(() => {
    const mediaID = this.selectedMediaID();
    if (mediaID === null) {
      return null;
    }
    return this.combinedMedia().find((media) => media.id === mediaID) || null;
  });

  /** Media item that comes before the currently selected media item in the filtered and sorted media list */
  readonly previousMedia = computed(() => {
    const mediaID = this.selectedMediaID();
    if (mediaID === null) {
      return null;
    }
    const mediaList = this.filteredSortedMedia();
    const currentIndex = mediaList.findIndex((media) => media.id === mediaID);
    if (currentIndex > 0) {
      return mediaList[currentIndex - 1];
    }
    return null;
  });

  /** Media item that comes after the currently selected media item in the filtered and sorted media list */
  readonly nextMedia = computed(() => {
    const mediaID = this.selectedMediaID();
    if (mediaID === null) {
      return null;
    }
    const mediaList = this.filteredSortedMedia();
    const currentIndex = mediaList.findIndex((media) => media.id === mediaID);
    if (currentIndex < mediaList.length - 1) {
      return mediaList[currentIndex + 1];
    }
    return null;
  });

  constructor() {
    // Subscribe to WebSocket updates to reload media data when necessary
    this.webSocketService.toastMessage.pipe(takeUntilDestroyed()).subscribe((msg) => {
      if (msg.reload?.includes('media')) {
        this.mediaResource.reload();
      }
      if (msg.reload?.includes('files')) {
        this.mediaFilesResource.reload();
      }
      if (msg.reload?.includes('downloads')) {
        this.mediaDownloadsResource.reload();
      }
    });
  }

  /**
   * Refreshes all media-related content by reloading the media, media files, and media downloads resources.
   *
   * @returns {void} This method does not return a value.
   */
  refreshContent(): void {
    this.mediaResource.reload();
    this.mediaFilesResource.reload();
    this.mediaDownloadsResource.reload();
  }

  /**
   * Handles the event when a media item is selected, either by checking or unchecking a checkbox.
   * Adds or removes the media item from the selectedMedia array based on the checkbox state.
   *
   * @param {Media} media - The media item that was selected.
   * @param {boolean} checked - Indicates whether the media item was checked or unchecked.
   * @returns {void}
   */
  onMediaChecked(media: Media, checked: boolean): void {
    if (checked) {
      this.checkedMediaIDs.update((ids) => [...ids, media.id]);
    } else {
      this.checkedMediaIDs.update((ids) => ids.filter((id) => id !== media.id));
    }
  }

  /**
   * Searches for media items that match the given search term.
   *
   * @param searchTerm - The term to search for within the media titles.
   * @returns An array of media items whose titles include the search term.
   */
  searchMedia(searchTerm: string): Observable<SearchMedia[]> {
    let url = `${this.mediaUrl}search`;
    let params = new HttpParams().set('query', searchTerm);
    return this.httpClient.get<SearchMedia[]>(url, {params: params});
  }

  /**
   * Updates the status of multiple media items in a batch operation.
   *
   * @param mediaIDs - An array of media item IDs to update.
   * @param action - The action to perform on the media items. \
   * Possible values are:
   * - `monitor`: Monitor the specified media items.
   * - `unmonitor`: Unmonitor the specified media items.
   * - `delete`: Delete the trailers for specified media items.
   * - `download`: Download the trailers specified media items.
   * @param profileID - The ID of the profile to use for the batch update. \
   * If not provided, defaults to -1. \
   * Only required for `download` action.
   * @returns An Observable that emits the response from the server.
   */
  batchUpdate(mediaIDs: number[], action: string, profileID: number = -1): Observable<any> {
    const url = `${this.mediaUrl}batch_update`;
    return this.httpClient.post(url, {
      media_ids: mediaIDs,
      action: action.toLowerCase(),
      profile_id: profileID,
    });
  }

  /**
   * Downloads a trailer for a Media item.
   *
   * @param mediaID - The ID of the Media item to download the trailer for.
   * @param profileID - The ID of the profile to use for downloading the trailer.
   * @param ytID - The YouTube ID of the trailer to download. Can be an empty string.
   * @returns - An Observable that emits the response from the server.
   * - If an error occurs during the request, the Observable will emit an error.
   */
  downloadMediaTrailer(mediaID: number, profileID: number, ytID: string): Observable<any> {
    const params = new HttpParams().set('profile_id', profileID).set('yt_id', ytID);
    const url = `${this.mediaUrl}${mediaID}/download`;
    return this.httpClient.post(url, {}, {params: params});
  }

  /**
   * Toggles the monitoring status of a Media item.
   *
   * @param mediaID - The ID of the Media item to toggle the monitoring status for.
   * @param monitor - If `true`, the Media item will be monitored. \
   * If `false`, the Media item will not be monitored.
   * @returns An Observable that emits the response from the server.
   * If an error occurs during the request, the Observable will emit an error.
   */
  monitorMedia(mediaID: number, monitor: boolean): Observable<any> {
    const params = new HttpParams().set('monitor', monitor);
    const url = `${this.mediaUrl}${mediaID}/monitor`;
    return this.httpClient.post(url, {}, {params: params});
  }

  /**
   * Deletes the trailer for a Media item.
   *
   * @param mediaID - The ID of the Media item to delete the trailer for.
   * @returns An Observable that emits the response from the server.
   * If an error occurs during the request, the Observable will emit an error.
   */
  deleteMediaTrailer(mediaID: number): Observable<any> {
    const url = `${this.mediaUrl}${mediaID}/trailer`;
    return this.httpClient.delete(url);
  }

  async fetchMediaFiles(mediaID: number): Promise<FolderInfo> {
    const url = `${this.mediaUrl}${mediaID}/files`;
    const files = await firstValueFrom(this.httpClient.get<FolderInfo>(url));
    return mapFolderInfo(files);
  }

  rescanMediaFiles(mediaID: number): Observable<any> {
    const url = `${this.mediaUrl}${mediaID}/rescan_files`;
    return this.httpClient.post(url, {});
  }

  /**
   * Searches for a media trailer by its ID.
   *
   * @param {number} mediaID - The ID of the media to search for.
   * @param {number} profileID - The ID of the profile to use for the search.
   * @returns {Observable<any>} An observable containing the search results.
   */
  searchMediaTrailer(mediaID: number, profileID: number): Observable<any> {
    const params = new HttpParams().set('profile_id', profileID);
    const url = `${this.mediaUrl}${mediaID}/search`;
    return this.httpClient.post(url, {}, {params: params});
  }

  /**
   * Saves the media trailer by sending a POST request to update the media with the given YouTube ID.
   *
   * @param {number} mediaID - The ID of the media to update.
   * @param {string} ytID - The YouTube ID of the trailer to be saved.
   * @returns {Observable<any>} An observable that emits the response from the server.
   */
  saveMediaTrailer(mediaID: number, ytID: string): Observable<any> {
    const url = `${this.mediaUrl}${mediaID}/update`;
    const params = new HttpParams().set('yt_id', ytID);
    return this.httpClient.post(url, {}, {params: params});
  }
}

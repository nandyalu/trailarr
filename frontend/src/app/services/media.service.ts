import {HttpClient, HttpParams} from '@angular/common/http';
import {inject, Injectable} from '@angular/core';
import {catchError, firstValueFrom, map, Observable, of} from 'rxjs';
import {environment} from '../../environment';
import {FolderInfo, mapFolderInfo, mapMedia, Media, SearchMedia} from '../models/media';

@Injectable({
  providedIn: 'root',
})
export class MediaService {
  private readonly httpClient = inject(HttpClient);

  private mediaUrl = environment.apiUrl + environment.media;

  // allMedia = signal<Media[]>([]);

  // Add a getter for the allMedia signal
  // getAllMedia() {
  //   return this.allMedia;
  // }

  /**
   * Fetches all media items from the server, maps them, and saves them to the allMedia signal.
   *
   * @param {boolean | null} moviesOnly
   * Flag to specify what Media items to fetch. Default is `null`.
   * - If `true`, only movies will be fetched.
   * - If `false`, only series will be fetched.
   * - If `null`, both movies and series will be fetched.
   * @param {string} [filterBy='all']
   * The field by which to filter the media items. Default is `'all'`. \
   * Possible values are:
   * - `all`: Fetch all media items.
   * - `downloaded`: Fetch only downloaded media items.
   * - `monitored`: Fetch only monitored media items.
   * - `missing`: Fetch only missing media items.
   * - `unmonitored`: Fetch only unmonitored media items.
   * @returns {void}
   */
  fetchAllMedia(moviesOnly: boolean | null, filterBy: string = 'all') {
    // Fetch all media items from the server, map them, and save them to the allMedia signal
    const url = `${this.mediaUrl}all`;
    let params: HttpParams;
    if (moviesOnly !== null) {
      params = new HttpParams().set('movies_only', moviesOnly).set('filter_by', filterBy);
    } else {
      params = new HttpParams().set('filter_by', filterBy);
    }
    return this.httpClient.get<any[]>(url, {params: params});
  }

  /**
   * Fetches updated media items from the server and updates the allMedia signal.
   *
   * @returns {void}
   */
  fetchUpdatedMedia(seconds: number) {
    // Fetch updated media items from the server and update the allMedia signal
    const url = `${this.mediaUrl}updated`;

    const params = new HttpParams().set('seconds', seconds);
    return this.httpClient.get<any[]>(url, {params: params});
  }

  /**
   * Fetches a list of recently downloaded media items. Max 50 items.
   *
   * @param moviesOnly - Flag to specify what Media items to fetch. \
   * - If `true`, only movies will be fetched. \
   * - If `false`, only series will be fetched. \
   * - If `null`, both movies and series will be fetched.
   * @returns An Observable that emits an array of Media objects.
   */
  fetchRecentlyDownloaded(moviesOnly: boolean | null): Observable<Media[]> {
    let url = `${this.mediaUrl}downloaded`;
    let params = new HttpParams();
    if (moviesOnly !== null) {
      params = new HttpParams().set('limit', '50').set('movies_only', moviesOnly);
    } else {
      params = new HttpParams().set('limit', '50');
    }
    // Else, Fetch the filtered media list from the server
    return this.httpClient.get<Media[]>(url, {params: params}).pipe(
      map((media_list: any[]) => {
        return media_list.map((media) => mapMedia(media));
      }),
    );
  }

  /**
   * Retrieves a media item by its ID from the server.
   *
   * @param mediaID - The ID of the media item to retrieve.
   * @returns An observable of the media item.
   */
  getMediaByID(mediaID: number): Observable<Media> {
    const url = `${this.mediaUrl}${mediaID}`;
    return this.httpClient.get<any>(url).pipe(map((media) => mapMedia(media)));
  }

  /**
   * Retrieves the previous media item in the list based on the provided media ID.
   *
   * @param {number} mediaID - The ID of the current media item.
   * @returns {Media | null} - The previous media item if it exists, otherwise null.
   */
  // getPreviousMedia(mediaID: number): Media | null {
  //   let mediaList = this.allMedia();
  //   let index = mediaList.findIndex(media => media.id === mediaID);
  //   if (index > 0) {
  //     return mediaList[index - 1];
  //   }
  //   return null;
  // }

  /**
   * Retrieves the next media item in the list based on the provided media ID.
   *
   * @param {number} mediaID - The ID of the current media item.
   * @returns {Media | null} - The next media item if it exists, otherwise null.
   */
  // getNextMedia(mediaID: number): Media | null {
  //   let mediaList = this.allMedia();
  //   let index = mediaList.findIndex(media => media.id === mediaID);
  //   if (index < mediaList.length - 1) {
  //     return mediaList[index + 1];
  //   }
  //   return null;
  // }

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
   * @returns An Observable that emits the response from the server.
   */
  batchUpdate(mediaIDs: number[], action: string): Observable<any> {
    const url = `${this.mediaUrl}batch_update`;
    return this.httpClient.post(url, {
      media_ids: mediaIDs,
      action: action.toLowerCase(),
    });
  }

  /**
   * Downloads a trailer for a Media item.
   *
   * @param mediaID - The ID of the Media item to download the trailer for.
   * @param ytID - The YouTube ID of the trailer to download. Can be an empty string.
   * @returns - An Observable that emits the response from the server.
   * - If an error occurs during the request, the Observable will emit an error.
   */
  downloadMediaTrailer(mediaID: number, ytID: string): Observable<any> {
    const params = new HttpParams().set('yt_id', ytID);
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

  /**
   * Fetches the files for a Media item.
   *
   * @param mediaID - The ID of the Media item to fetch the files for.
   * @returns An Observable that emits a `FolderInfo` object with the files for the specified Media item. \
   * If no files are found for the specified Media item, the Observable will emit a string. \
   * If an error occurs during the request, the Observable will emit an error.
   */
  getMediaFiles(mediaID: number): Observable<any> {
    const url = `${this.mediaUrl}${mediaID}/files`;
    return this.httpClient.get(url).pipe(
      map((response) => {
        if (typeof response === 'string') {
          // Handle the string response
          return response;
        } else {
          // Map the FolderInfo object
          return mapFolderInfo(response);
        }
      }),
      catchError((error) => {
        // Handle error appropriately
        console.error('Error fetching media files:', error);
        return of(`Error: ${error.message}`);
      }),
    );
  }

  async fetchMediaFiles(mediaID: number): Promise<FolderInfo> {
    const url = `${this.mediaUrl}${mediaID}/files`;
    const files = await firstValueFrom(this.httpClient.get<FolderInfo>(url));
    return mapFolderInfo(files);
  }

  /**
   * Searches for a media trailer by its ID.
   *
   * @param {number} mediaID - The ID of the media to search for.
   * @returns {Observable<any>} An observable containing the search results.
   */
  searchMediaTrailer(mediaID: number): Observable<any> {
    const url = `${this.mediaUrl}${mediaID}/search`;
    return this.httpClient.post(url, {});
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

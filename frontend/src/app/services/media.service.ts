import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { catchError, map, Observable, of } from 'rxjs';
import { environment } from '../../environment';
import { mapFolderInfo, mapMedia, Media, SearchMedia } from '../models/media';

@Injectable({
  providedIn: 'root'
})
export class MediaService {

  private mediaUrl = environment.apiUrl + environment.media;

  constructor(private http: HttpClient) { }

  /**
   * Fetches all media items from the server with optional filtering and sorting.
   *
   * @param moviesOnly - Flag to specify what Media items to fetch. \
   * - If `true`, only movies will be fetched. \
   * - If `false`, only series will be fetched. \
   * - If `null`, both movies and series will be fetched.
   * @param filterBy - The field by which to filter the media items. \
   * Can be `all`, `downloaded`, `monitored`, `missing`, or `unmonitored`.
   * @param sortBy - The field by which to sort the media items. \
   * Can be `title`, `year`, `added_at`, or `updated_at`.
   * @param sortAsc - If `true`, the media items will be sorted in ascending order. \
   * - If `false`, they will be sorted in descending order. \
   * - Default is `true`.
   * @returns An Observable that emits an array of Media objects.
   */
  getAllMedia(
    moviesOnly: boolean | null,
    filterBy: string,
    sortBy: string,
    sortAsc: boolean = true
  ): Observable<Media[]> {
    const getMediaUrl = `${this.mediaUrl}all?movies_only=${moviesOnly}&filter_by=${filterBy}&sort_by=${sortBy}&sort_asc=${sortAsc}`;
    return this.http.get<Media[]>(`${getMediaUrl}`).pipe(
      map((media_list: any[]) => media_list.map(media => mapMedia(media)))
    );
  }

  /**
   * Fetches a list of recent media items. Max 50 items.
   * 
   * @param moviesOnly - Flag to specify what Media items to fetch. \
   * - If `true`, only movies will be fetched. \
   * - If `false`, only series will be fetched. \
   * - If `null`, both movies and series will be fetched.
   * @returns An Observable that emits an array of Media objects.
   */
  getRecentMedia(moviesOnly: boolean | null): Observable<Media[]> {
    const getMediaUrl = `${this.mediaUrl}?limit=50&movies_only=${moviesOnly}`;
    return this.http.get<Media[]>(`${getMediaUrl}`).pipe(
      map((media_list: any[]) => media_list.map(media => mapMedia(media)))
    );
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
  getRecentlyDownloaded(moviesOnly: boolean | null): Observable<Media[]> {
    const getMediaUrl = `${this.mediaUrl}downloaded?limit=50&movies_only=${moviesOnly}`;
    return this.http.get<Media[]>(`${getMediaUrl}`).pipe(
      map((media_list: any[]) => media_list.map(media => mapMedia(media)))
    );
  }

  /**
   * Fetches a single Media item by its ID.
   * 
   * @param id - The ID of the Media item to fetch.
   * @returns - An Observable that emits a single Media object with the specified ID.
   * - If no Media item is found with the specified ID, the Observable will emit `null`.
   * - If an error occurs during the request, the Observable will emit an error.
   */
  getMediaById(id: number): Observable<Media> {
    return this.http.get<Media>(`${this.mediaUrl}${id}`).pipe(
      map(media => mapMedia(media))
    );
  }

  /**
   * Downloads a trailer for a Media item.
   * 
   * @param id - The ID of the Media item to download the trailer for.
   * @param yt_id - The YouTube ID of the trailer to download. Can be an empty string.
   * @returns - An Observable that emits the response from the server.
   * - If an error occurs during the request, the Observable will emit an error.
   */
  downloadMediaTrailer(id: number, yt_id: string): Observable<any> {
    return this.http.post(`${this.mediaUrl}${id}/download?yt_id=${yt_id}`, {});
  }

  /**
   * Toggles the monitoring status of a Media item.
   * 
   * @param id - The ID of the Media item to toggle the monitoring status for.
   * @param monitor - If `true`, the Media item will be monitored. \
   * If `false`, the Media item will not be monitored.
   * @returns An Observable that emits the response from the server.
   * If an error occurs during the request, the Observable will emit an error.
   */
  monitorMedia(id: number, monitor: boolean): Observable<any> {
    return this.http.post(`${this.mediaUrl}${id}/monitor?monitor=${monitor}`, {});
  }

  /**
   * Deletes the trailer for a Media item.
   * 
   * @param id - The ID of the Media item to delete the trailer for.
   * @returns An Observable that emits the response from the server.
   * If an error occurs during the request, the Observable will emit an error.
   */
  deleteMediaTrailer(id: number): Observable<any> {
    return this.http.delete(`${this.mediaUrl}${id}/trailer`);
  }

  /**
   * Fetches the files for a Media item.
   * 
   * @param id - The ID of the Media item to fetch the files for.
   * @returns An Observable that emits a `FolderInfo` object with the files for the specified Media item. \
   * If no files are found for the specified Media item, the Observable will emit a string. \
   * If an error occurs during the request, the Observable will emit an error.
   */
  getMediaFiles(id: number): Observable<any> {
    return this.http.get(`${this.mediaUrl}${id}/files`).pipe(
      map(response => {
        if (typeof response === 'string') {
          // Handle the string response
          return response;
        } else {
          // Map the FolderInfo object
          return mapFolderInfo(response);
        }
      }),
      catchError(error => {
        // Handle error appropriately
        console.error('Error fetching media files:', error);
        return of(`Error: ${error.message}`);
      })
    );
  }

  searchMedia(query: string): Observable<SearchMedia[]> {
    return this.http.get<SearchMedia[]>(`${this.mediaUrl}search?query=${query}`);
  }
}

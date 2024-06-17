import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../environment';
import { FolderInfo, Media, mapFolderInfo, mapMedia } from '../models/media';

@Injectable({
  providedIn: 'root'
})
export class SeriesService {

  private seriesUrl = environment.apiUrl + environment.series;

  constructor(private http: HttpClient) { }

  getRecentMedia(): Observable<Media[]> {
    return this.http.get<Media[]>(this.seriesUrl).pipe(
      map(series_list => series_list.map(series => mapMedia(series, false)))
    );
  }

  getMediaById(id: number): Observable<Media> {
    return this.http.get<Media>(`${this.seriesUrl}${id}`).pipe(
      map(series => mapMedia(series, false))
    );
  }

  downloadMediaTrailer(id: number, yt_id: string): Observable<any> {
    return this.http.post(`${this.seriesUrl}${id}/download?yt_id=${yt_id}`, {});
  }

  monitorMedia(id: number, monitor: boolean): Observable<any> {
    return this.http.post(`${this.seriesUrl}${id}/monitor?monitor=${monitor}`, {});
  }

  deleteMediaTrailer(id: number): Observable<any> {
    return this.http.delete(`${this.seriesUrl}${id}/trailer`);
  }

  getMediaFiles(id: number): Observable<FolderInfo> {
    return this.http.get<FolderInfo>(`${this.seriesUrl}${id}/files`).pipe(
      map(folder => mapFolderInfo(folder))
    );
  }

}
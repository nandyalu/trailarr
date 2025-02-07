import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environment';
import { VideoInfo } from '../models/files';

@Injectable({
  providedIn: 'root'
})
export class FilesService {

  private files_url = environment.apiUrl + environment.files;

  constructor(
    private httpClient: HttpClient
  ) { }

  getTextFile(file_path: string): Observable<string> {
    const params1 = new HttpParams()
      .set('file_path', file_path);
    const url = this.files_url + 'read';
    return this.httpClient.get<string>(url, { params: params1 });
  }

  getVideoInfo(file_path: string): Observable<VideoInfo> {
    const params1 = new HttpParams()
      .set('file_path', file_path);
    const url = this.files_url + 'video_info';
    return this.httpClient.get<VideoInfo>(url, { params: params1 });
  }

  // removeTracks(file_path: string): Observable<string> {
  //   const params1 = new HttpParams()
  //     .set('file_path', file_path);
  //   const url = this.files_url + 'remove_tracks';
  //   return this.httpClient.get<string>(url, { params: params1 });
  // }

  deleteFileFolder(path: string, mediaID: number = -1): Observable<boolean> {
    const params = new HttpParams()
      .set('path', path)
      .set('media_id', mediaID);
    const url = this.files_url + 'delete';
    return this.httpClient.delete<boolean>(url, { params });
  }

  renameFileFolder(old_path: string, new_path: string): Observable<boolean> {
    const params = new HttpParams()
      .set('old_path', old_path)
      .set('new_path', new_path);
    const url = this.files_url + 'rename';
    return this.httpClient.post<boolean>(url, {}, { params });
  }
}

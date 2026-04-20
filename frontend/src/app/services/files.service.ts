import {HttpClient} from '@angular/common/http';
import {inject, Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {FolderInfo} from '../models/settings';
import {VideoInfo} from '../models/video';
import {environment} from '../../environment';

@Injectable({providedIn: 'root'})
export class FilesService {
  private readonly http = inject(HttpClient);
  private readonly filesUrl = environment.apiUrl + environment.files;

  getFilesSimple(path: string): Observable<FolderInfo[]> {
    return this.http.get<FolderInfo[]>(this.filesUrl + 'files_simple', {params: {path}});
  }

  readFile(file_path: string): Observable<string> {
    return this.http.get<string>(this.filesUrl + 'read', {params: {file_path}});
  }

  getVideoInfo(file_path: string): Observable<VideoInfo | null> {
    return this.http.get<VideoInfo | null>(this.filesUrl + 'video_info', {params: {file_path}});
  }

  trimVideo(file_path: string, output_file: string, start_timestamp: number | string, end_timestamp: number | string): Observable<string> {
    return this.http.post<string>(this.filesUrl + 'trim_video', null, {
      params: {file_path, output_file, start_timestamp: String(start_timestamp), end_timestamp: String(end_timestamp)},
    });
  }

  renameFileFol(old_path: string, new_path: string): Observable<boolean> {
    return this.http.post<boolean>(this.filesUrl + 'rename', null, {params: {old_path, new_path}});
  }

  deleteFileFol(path: string, media_id?: number): Observable<boolean> {
    const params: Record<string, string | number> = {path};
    if (media_id !== undefined) params['media_id'] = media_id;
    return this.http.delete<boolean>(this.filesUrl + 'delete', {params});
  }
}

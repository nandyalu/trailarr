import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Observable, catchError, map, of } from "rxjs";
import { environment } from "../../environment";
import { FolderInfo, Media, mapFolderInfo, mapMedia } from "../models/media";

@Injectable({
    providedIn: 'root'
})
export class MovieService {

    private moviesUrl = environment.apiUrl + environment.movies;

    constructor(private http: HttpClient) { }

    getAllMedia(): Observable<Media[]> {
        return this.http.get<Media[]>(`${this.moviesUrl}all`).pipe(
            map((movie_list: any[]) => movie_list.map(movie => mapMedia(movie)))
        );
    }

    getRecentMedia(): Observable<Media[]> {
        return this.http.get<Media[]>(`${this.moviesUrl}?limit=50`).pipe(
            map((movie_list: any[]) => movie_list.map(movie => mapMedia(movie)))
        );
    }

    getRecentlyDownloaded(): Observable<Media[]> {
        return this.http.get<Media[]>(`${this.moviesUrl}downloaded?limit=50`).pipe(
            map((movie_list: any[]) => movie_list.map(movie => mapMedia(movie)))
        );
    }

    getMediaById(id: number): Observable<Media> {
        return this.http.get<Media>(`${this.moviesUrl}${id}`).pipe(
            map(movie => mapMedia(movie))
        );
    }

    downloadMediaTrailer(id: number, yt_id: string): Observable<any> {
        return this.http.post(`${this.moviesUrl}${id}/download?yt_id=${yt_id}`, {});
    }

    monitorMedia(id: number, monitor: boolean): Observable<any> {
        return this.http.post(`${this.moviesUrl}${id}/monitor?monitor=${monitor}`, {});
    }

    deleteMediaTrailer(id: number): Observable<any> {
        return this.http.delete(`${this.moviesUrl}${id}/trailer`);
    }

    getMediaFiles(id: number): Observable<FolderInfo | string> {
        return this.http.get<FolderInfo>(`${this.moviesUrl}${id}/files`).pipe(
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

}
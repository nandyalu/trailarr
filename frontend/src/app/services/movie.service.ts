import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Observable, map } from "rxjs";
import { environment } from "../../environment";
import { FolderInfo, Media, mapFolderInfo, mapMedia } from "../models/media";

@Injectable({
    providedIn: 'root'
})
export class MovieService {

    private moviesUrl = environment.apiUrl + environment.movies;

    constructor(private http: HttpClient) { }

    getRecentMedia(): Observable<Media[]> {
        return this.http.get<Media[]>(this.moviesUrl).pipe(
            map((movie_list: any[]) => movie_list.map(movie => mapMedia(movie, true)))
        );
    }

    getRecentlyDownloaded(): Observable<Media[]> {
        return this.http.get<Media[]>(`${this.moviesUrl}downloaded`).pipe(
            map((movie_list: any[]) => movie_list.map(movie => mapMedia(movie, movie.is_movie)))
        );
    }

    getMediaById(id: number): Observable<Media> {
        return this.http.get<Media>(`${this.moviesUrl}${id}`).pipe(
            map(movie => mapMedia(movie, true))
        );
    }

    downloadMediaTrailer(id: number, yt_id: string): Observable<any> {
        return this.http.post(
            `${this.moviesUrl}${id}/download`,
            { params: { yt_id: yt_id } }
        );
    }

    monitorMedia(id: number, monitor: boolean): Observable<any> {
        return this.http.post(
            `${this.moviesUrl}${id}/monitor`,
            {params: { monitor: monitor } }
        );
    }

    deleteMediaTrailer(id: number): Observable<any> {
        return this.http.delete(`${this.moviesUrl}${id}/trailer`);
    }

    getMediaFiles(id: number): Observable<FolderInfo> {
        return this.http.get<FolderInfo>(`${this.moviesUrl}${id}/files`).pipe(
            map(folder => mapFolderInfo(folder))
        );
    }

}
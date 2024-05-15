import { HttpClient } from "@angular/common/http";
import { Injectable } from "@angular/core";
import { Observable, map } from "rxjs";
import { environment } from "../../environment";
import { Media } from "../models/media";

@Injectable({
    providedIn: 'root'
})
export class MovieService {

    private moviesUrl = environment.apiUrl + environment.movies;

    constructor(private http: HttpClient) { }

    getMovies(): Observable<Media[]> {
        return this.http.get<Media[]>(this.moviesUrl).pipe(
            map((movies: any[]) => movies.map(movie => ({
                ...movie,
                added_at: new Date(movie.added_at),
                updated_at: new Date(movie.updated_at),
                created_at: new Date(movie.created_at)
            })))
        );
    }
}
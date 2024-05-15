import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../environment';
import { Media } from '../models/media';

@Injectable({
  providedIn: 'root'
})
export class SeriesService {

  private seriesUrl = environment.apiUrl + environment.series;

  constructor(private http: HttpClient) { }

  getSeries(): Observable<Media[]> {
    return this.http.get<Media[]>(this.seriesUrl).pipe(
      map((series: any[]) => series.map(serie => ({
        ...serie,
        added_at: new Date(serie.added_at),
        updated_at: new Date(serie.updated_at),
        created_at: new Date(serie.created_at)
      })))
    );
  }
}

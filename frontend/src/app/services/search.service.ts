import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environment';
import { SearchMedia } from '../models/media';

@Injectable({
  providedIn: 'root'
})
export class SearchService {

  private searchUrl = environment.apiUrl + environment.search;

  constructor(private http: HttpClient) { }

  searchMedia(query: string): Observable<SearchMedia[]> {
    return this.http.get<SearchMedia[]>(`${this.searchUrl}${query}`);
  }
}

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environment';
import { CustomFilter, CustomFilterCreate } from '../models/customfilter';

@Injectable({
  providedIn: 'root'
})
export class CustomfilterService {

  private cp_url = environment.apiUrl + environment.customfilters;

  constructor(
    private httpClient: HttpClient
  ) { }

  create(customFilter: CustomFilterCreate): Observable<CustomFilter> {
    return this.httpClient.post<CustomFilter>(this.cp_url, customFilter);
  }

  update(customFilter: CustomFilter): Observable<CustomFilter> {
    const url = this.cp_url + customFilter.id;
    return this.httpClient.put<CustomFilter>(url, customFilter);
  }

  delete(id: number): Observable<boolean> {
    const url = this.cp_url + id;
    return this.httpClient.delete<boolean>(url);
  }

  getHomeFilters(): Observable<CustomFilter[]> {
    const url = this.cp_url + 'home';
    return this.httpClient.get<CustomFilter[]>(url);
  }

  getMovieFilters(): Observable<CustomFilter[]> {
    const url = this.cp_url + 'movie';
    return this.httpClient.get<CustomFilter[]>(url);
  }

  getSeriesFilters(): Observable<CustomFilter[]> {
    const url = this.cp_url + 'series';
    return this.httpClient.get<CustomFilter[]>(url);
  }
}

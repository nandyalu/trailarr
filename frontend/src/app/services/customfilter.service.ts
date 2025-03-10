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

  getViewFilters(moviesOnly: boolean | null): Observable<CustomFilter[]> {
    const view = moviesOnly == null ? 'home' : (moviesOnly ? 'movie' : 'series');
    const url = this.cp_url + view;
    return this.httpClient.get<CustomFilter[]>(url);
  }
}

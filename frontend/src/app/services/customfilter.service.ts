import {HttpClient} from '@angular/common/http';
import {inject, Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {environment} from '../../environment';
import {CustomFilter, CustomFilterCreate, FilterType} from '../models/customfilter';
import { TrailerProfileCreate } from 'generated-sources/openapi';

@Injectable({
  providedIn: 'root',
})
export class CustomfilterService {
  private readonly httpClient = inject(HttpClient);

  private cf_url = environment.apiUrl + environment.customfilters;

  create(customFilter: CustomFilterCreate): Observable<CustomFilter> {
    if (customFilter.filter_type === FilterType.TRAILER) {
      const profileUrl = environment.apiUrl + environment.profiles;
      const profileCreate = {
        customfilter: customFilter,
      } as unknown as TrailerProfileCreate;
      return this.httpClient.post<CustomFilter>(profileUrl, profileCreate);
    }
    return this.httpClient.post<CustomFilter>(this.cf_url, customFilter);
  }

  update(customFilter: CustomFilter): Observable<CustomFilter> {
    const url = this.cf_url + customFilter.id;
    return this.httpClient.put<CustomFilter>(url, customFilter);
  }

  delete(id: number): Observable<boolean> {
    const url = this.cf_url + id;
    return this.httpClient.delete<boolean>(url);
  }

  getViewFilters(moviesOnly: boolean | null): Observable<CustomFilter[]> {
    const view = moviesOnly == null ? 'home' : moviesOnly ? 'movie' : 'series';
    const url = this.cf_url + view;
    return this.httpClient.get<CustomFilter[]>(url);
  }
}

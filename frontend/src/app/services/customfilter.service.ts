import {HttpClient, httpResource} from '@angular/common/http';
import {computed, inject, Injectable, signal} from '@angular/core';
import {TrailerProfileCreate} from 'generated-sources/openapi';
import {Observable} from 'rxjs';
import {environment} from '../../environment';
import {CustomFilter, CustomFilterCreate, FilterType} from '../models/customfilter';

@Injectable({
  providedIn: 'root',
})
export class CustomfilterService {
  private readonly httpClient = inject(HttpClient);

  private cf_url = environment.apiUrl + environment.customfilters;

  readonly filtersResource = httpResource<CustomFilter[]>(() => this.cf_url, {defaultValue: []});

  readonly moviesOnly = signal<boolean | null>(null);
  readonly viewFilters = computed(() => {
    let _moviesOnly = this.moviesOnly();
    const filterType = _moviesOnly === null ? FilterType.HOME : _moviesOnly ? FilterType.MOVIES : FilterType.SERIES;
    const filters = this.filtersResource.value();
    return filters.filter((f) => f.filter_type === filterType);
  });

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

  reloadFilters(): void {
    this.filtersResource.reload();
  }
}

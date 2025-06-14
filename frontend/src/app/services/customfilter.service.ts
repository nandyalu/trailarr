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

  readonly homeFiltersResource = httpResource<CustomFilter[]>(this.cf_url + 'home', {defaultValue: []});
  readonly moviesFiltersResource = httpResource<CustomFilter[]>(this.cf_url + 'movie', {defaultValue: []});
  readonly seriesFiltersResource = httpResource<CustomFilter[]>(this.cf_url + 'series', {defaultValue: []});

  readonly moviesOnly = signal<boolean | null>(null);
  readonly viewFilters = computed(() => {
    let _moviesOnly = this.moviesOnly();
    switch (_moviesOnly) {
      case true: {
        return this.moviesFiltersResource.value();
      }
      case false: {
        return this.seriesFiltersResource.value();
      }
      case null: {
        return this.homeFiltersResource.value();
      }
    }
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

  getViewFilters(moviesOnly: boolean | null): Observable<CustomFilter[]> {
    const view = moviesOnly == null ? 'home' : moviesOnly ? 'movie' : 'series';
    const url = this.cf_url + view;
    return this.httpClient.get<CustomFilter[]>(url);
  }

  reloadFilters(): void {
    const _moviesOnly = this.moviesOnly();
    if (_moviesOnly === null) {
      this.homeFiltersResource.reload();
    } else if (_moviesOnly) {
      this.moviesFiltersResource.reload();
    } else {
      this.seriesFiltersResource.reload();
    }
  }
}

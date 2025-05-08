import {CommonModule} from '@angular/common';
import {Component, inject, signal} from '@angular/core';
import {RouterLink} from '@angular/router';
import {TrailerProfileRead, TrailerProfilesService} from 'generated-sources/openapi';
import {catchError, distinctUntilChanged, of, shareReplay, startWith, Subject, switchMap, tap} from 'rxjs';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {RouteAdd, RouteEdit, RouteProfiles, RouteSettings} from 'src/routing';
import {jsonEqual} from 'src/util';

@Component({
  selector: 'app-show-profiles',
  imports: [CommonModule, LoadIndicatorComponent, RouterLink],
  templateUrl: './show-profiles.component.html',
  styleUrl: './show-profiles.component.scss',
})
export class ShowProfilesComponent {
  private readonly profilesService = inject(TrailerProfilesService);

  protected readonly isLoading = signal(true);
  private readonly triggerReload$ = new Subject<void>();

  protected readonly RouteAdd = RouteAdd;
  protected readonly RouteProfiles = RouteProfiles;
  protected readonly RouteEdit = RouteEdit;
  protected readonly RouteSettings = RouteSettings;

  protected readonly profiles$ = this.triggerReload$.pipe(
    startWith('meh'),
    tap(() => this.isLoading.set(true)),
    switchMap(() =>
      this.profilesService.getTrailerProfilesApiV1TrailerprofilesGet().pipe(
        catchError((err) => {
          console.log('Failed to load profiles.', err);
          return of<TrailerProfileRead[]>([]);
        }),
      ),
    ),
    tap(() => this.isLoading.set(false)),
    distinctUntilChanged(jsonEqual),
    shareReplay({refCount: true, bufferSize: 1}),
  );

  ngOnDestroy() {
    this.triggerReload$.complete();
  }
}

import {CommonModule} from '@angular/common';
import {ChangeDetectionStrategy, Component, inject, signal} from '@angular/core';
import {RouterLink} from '@angular/router';
import {Subject} from 'rxjs';
import {SettingsService} from 'src/app/services/settings.service';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {RouteAdd, RouteConnections, RouteEdit, RouteSettings} from 'src/routing';

@Component({
  selector: 'app-show-connections',
  templateUrl: './show-connections.component.html',
  styleUrl: './show-connections.component.scss',
  imports: [CommonModule, LoadIndicatorComponent, RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ShowConnectionsComponent {
  private readonly settingsService = inject(SettingsService);

  protected readonly connectionsResource = this.settingsService.connectionsResource;
  protected readonly isLoading = this.connectionsResource.isLoading;

  private readonly triggerReload$ = new Subject<void>();

  resultMessage = signal<string>('');
  resultType = signal<string>('');
  selectedId = 0;

  protected readonly RouteAdd = RouteAdd;
  protected readonly RouteConnections = RouteConnections;
  protected readonly RouteEdit = RouteEdit;
  protected readonly RouteSettings = RouteSettings;

  // protected readonly connections$ = this.triggerReload$.pipe(
  //   startWith('meh'),
  //   tap(() => this.isLoading.set(true)),
  //   switchMap(() =>
  //     this.connectionsService.getConnectionsApiV1ConnectionsGet().pipe(
  //       catchError((err) => {
  //         console.log('Failed to load connections.', err);
  //         return of<ConnectionRead[]>([]);
  //       }),
  //     ),
  //   ),
  //   tap(() => this.isLoading.set(false)),
  //   distinctUntilChanged(jsonEqual),
  //   shareReplay({refCount: true, bufferSize: 1}),
  // );

  // ngOnDestroy() {
  //   this.triggerReload$.complete();
  // }
}

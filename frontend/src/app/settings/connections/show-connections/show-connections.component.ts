import {CommonModule} from '@angular/common';
import {Component, ElementRef, inject, OnDestroy, signal, viewChild} from '@angular/core';
import {RouterLink} from '@angular/router';
import {ConnectionRead, ConnectionsService} from 'generated-sources/openapi';
import {catchError, distinctUntilChanged, of, shareReplay, startWith, Subject, switchMap, tap} from 'rxjs';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {RouteAdd, RouteConnections, RouteEdit, RouteSettings} from 'src/routing';
import {jsonEqual} from 'src/util';

@Component({
  selector: 'app-show-connections',
  templateUrl: './show-connections.component.html',
  styleUrl: './show-connections.component.scss',
  imports: [CommonModule, LoadIndicatorComponent, RouterLink],
})
export class ShowConnectionsComponent implements OnDestroy {
  private readonly connectionsService = inject(ConnectionsService);

  protected readonly isLoading = signal(true);

  private readonly triggerReload$ = new Subject<void>();

  resultMessage = '';
  resultType = '';
  selectedId = 0;

  protected readonly RouteAdd = RouteAdd;
  protected readonly RouteConnections = RouteConnections;
  protected readonly RouteEdit = RouteEdit;
  protected readonly RouteSettings = RouteSettings;

  private readonly dialog = viewChild<ElementRef<HTMLDialogElement>>('deleteConnectionDialog');

  protected readonly connections$ = this.triggerReload$.pipe(
    startWith('meh'),
    tap(() => this.isLoading.set(true)),
    switchMap(() =>
      this.connectionsService.getConnectionsApiV1ConnectionsGet().pipe(
        catchError((err) => {
          console.log('Failed to load connections.', err);
          return of<ConnectionRead[]>([]);
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

  protected closeDeleteDialog = () => this.dialog()?.nativeElement.close();
  protected showDeleteDialog = () => this.dialog()?.nativeElement.showModal();

  protected onConfirmDelete() {
    this.closeDeleteDialog();
    this.connectionsService
      .deleteConnectionApiV1ConnectionsConnectionIdDelete({connection_id: this.selectedId})
      .pipe(
        catchError((error) => {
          let errorMessage = '';
          if (error.error instanceof ErrorEvent) {
            // client-side error
            errorMessage = `Error: ${error.error.message}`;
          } else {
            // server-side error
            errorMessage = `Error: ${error.status} ${error.error.detail}`;
          }
          return of(errorMessage);
        }),
      )
      .subscribe((res) => {
        this.resultType = 'error';
        if (res.toLowerCase().includes('success')) {
          this.resultType = 'success';
        }
        this.resultMessage = res;
        this.triggerReload$.next();
        setTimeout(() => {
          this.resultMessage = '';
        }, 3000);
      });
  }
}

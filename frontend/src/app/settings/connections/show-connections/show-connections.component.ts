import {CommonModule} from '@angular/common';
import {ChangeDetectionStrategy, Component, inject, signal} from '@angular/core';
import {RouterLink} from '@angular/router';
import {ConnectionService} from 'src/app/services/connection.service';
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
  private readonly connectionService = inject(ConnectionService);

  protected readonly connectionsResource = this.connectionService.connectionsResource;
  protected readonly isLoading = this.connectionsResource.isLoading;

  resultMessage = signal<string>('');
  resultType = signal<string>('');
  selectedId = 0;

  protected readonly RouteAdd = RouteAdd;
  protected readonly RouteConnections = RouteConnections;
  protected readonly RouteEdit = RouteEdit;
  protected readonly RouteSettings = RouteSettings;
}

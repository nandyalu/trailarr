import {ChangeDetectionStrategy, Component} from '@angular/core';
import {RouterOutlet} from '@angular/router';

@Component({
  selector: 'app-connections',
  imports: [RouterOutlet],
  templateUrl: './connections.component.html',
  styleUrl: './connections.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConnectionsComponent {}

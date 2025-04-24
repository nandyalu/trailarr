import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-connections',
  imports: [RouterOutlet],
  templateUrl: './connections.component.html',
  // changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ConnectionsComponent {}

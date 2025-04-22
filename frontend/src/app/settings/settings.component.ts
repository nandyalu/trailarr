import {ChangeDetectionStrategy, Component} from '@angular/core';
import {RouterLink, RouterLinkActive, RouterOutlet} from '@angular/router';
import {RouteAbout, RouteConnections, RouteTrailer} from 'src/routing';

@Component({
  selector: 'app-settings',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SettingsComponent {
  protected readonly RouteAbout = RouteAbout;
  protected readonly RouteConnections = RouteConnections;
  protected readonly RouteTrailer = RouteTrailer;
}

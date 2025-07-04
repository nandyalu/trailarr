import {ChangeDetectionStrategy, Component, inject} from '@angular/core';
import {NavigationEnd, Router, RouterLink, RouterLinkActive} from '@angular/router';
import {RouteHome, RouteLogs, RouteMedia, RouteMovies, RouteSeries, RouteSettings, RouteTasks} from 'src/routing';

@Component({
  selector: 'app-sidenav',
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidenav.component.html',
  styleUrl: './sidenav.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SidenavComponent {
  protected readonly RouteHome = RouteHome;
  protected readonly RouteLogs = RouteLogs;
  protected readonly RouteMedia = RouteMedia;
  protected readonly RouteMovies = RouteMovies;
  protected readonly RouteSeries = RouteSeries;
  protected readonly RouteSettings = RouteSettings;
  protected readonly RouteTasks = RouteTasks;

  protected readonly router = inject(Router);

  previousUrl = '';
  currentUrl = '';

  constructor() {
    this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd) {
        this.previousUrl = this.currentUrl;
        this.currentUrl = event.url;
      }
    });
  }

  isActiveLink(link: string) {
    // Using a custom check to set active tab in nav, based on current and previous URLs.
    // If user navigates to a media details page, previously selected tab will be shown as active.
    return (this.previousUrl.includes(link) && this.currentUrl.includes(RouteMedia)) || this.currentUrl.includes(link);
  }
}

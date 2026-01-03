import {ChangeDetectionStrategy, Component, computed, inject, signal} from '@angular/core';
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
  protected readonly previousUrl = signal('');
  protected readonly currentUrl = signal('');

  /** Using a custom check to set active tab in nav, based on current and previous URLs.
    If user navigates to a media details page, previously selected tab will be shown as active.
  */
  protected readonly activeLink = computed(() => {
    const current = this.currentUrl();
    const previous = this.previousUrl();

    if (current.includes(RouteHome)) return RouteHome;
    if (current.includes(RouteMovies)) return RouteMovies;
    if (current.includes(RouteSeries)) return RouteSeries;

    // On media details page, keep previous tab active
    if (current.includes(RouteMedia)) {
      if (previous.includes(RouteMovies)) return RouteMovies;
      if (previous.includes(RouteSeries)) return RouteSeries;
      // Fallback to home if no previous tab found
      return RouteHome;
    }

    return '';
  });

  constructor() {
    this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd) {
        // Only update previousUrl if current page is not a media details page
        // This preserves the original tab when navigating between media details
        if (!this.currentUrl().includes(RouteMedia)) {
          this.previousUrl.set(this.currentUrl());
        }
        this.currentUrl.set(event.url);
      }
    });
  }
}

import {ChangeDetectionStrategy, Component} from '@angular/core';
import {RouterLink, RouterLinkActive} from '@angular/router';
import {RouteHome, RouteLogs, RouteMovies, RouteSeries, RouteSettings, RouteTasks} from 'src/routing';

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
  protected readonly RouteMovies = RouteMovies;
  protected readonly RouteSeries = RouteSeries;
  protected readonly RouteSettings = RouteSettings;
  protected readonly RouteTasks = RouteTasks;

  // isMenuCollapsed = true;
  // activeNavId = 1;
  // @ViewChildren('navLink') navLinks: QueryList<ElementRef> = new QueryList();
  // private selectedButton: HTMLAnchorElement | null = null;
  // constructor(private renderer: Renderer2, private router: Router) {
  //   this.router.events.pipe(
  //     filter(event => event instanceof NavigationEnd)
  //   ).subscribe(() => {
  //     this.updateActiveLink();
  //   });
  // }
  // ngAfterViewInit() {
  //   this.updateActiveLink();
  // }
  // updateActiveLink() {
  //   const URLpath = this.router.url.split('/')[1] || '/';
  //   this.navLinks.forEach((navLink) => {
  //     const href = (navLink.nativeElement as HTMLAnchorElement).href;
  //     const hrefPath = '/' + new URL(href).pathname.split('/')[1] || '/';
  //     // console.log('Path: %s, Href: %s', URLpath, hrefPath)
  //     if (hrefPath === URLpath) {
  //       this.renderer.addClass(navLink.nativeElement, 'active');
  //       this.selectedButton = navLink.nativeElement;
  //     }
  //   });
  // }
  // navigate(event: Event) {
  //   // Prevent default action
  //   event.preventDefault();
  //   // Get link element and set active class
  //   const selectedNavLink = event.currentTarget as HTMLAnchorElement;
  //   if (this.selectedButton) {
  //     this.renderer.removeClass(this.selectedButton, 'active');
  //   }
  //   this.renderer.addClass(selectedNavLink, 'active');
  //   this.selectedButton = selectedNavLink;
  //   // Get href and navigate to route
  //   const href = (event.currentTarget as HTMLAnchorElement).href;
  //   const path = new URL(href).pathname;
  //   var route = '/home';
  //   if (path !== '/') {
  //     route = '/' + path.split('/').filter(Boolean).shift() || '/home';
  //   }
  //   // this.router.navigate([route]);
  //   console.log('Clicked on link: %s, Navigating to Route: %s', href, route);
  // }
  // onRefresh() {
  //   throw new Error('Method not implemented.');
  // }
}

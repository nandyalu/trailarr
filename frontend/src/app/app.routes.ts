import {Routes} from '@angular/router';
import {RouteActivity, RouteEvents, RouteHome, RouteLogs, RouteMedia, RouteMovies, RouteParamMediaId, RouteSeries, RouteSettings, RouteTasks} from '../routing';
import {authGuard} from './auth/auth.guard';
import {LoginComponent} from './auth/login/login.component';

export const routes: Routes = [
  {path: 'login', component: LoginComponent},
  {path: RouteMedia, redirectTo: RouteHome, pathMatch: 'full'},
  {path: RouteHome, canActivate: [authGuard], loadChildren: () => import('./media/routes')},
  {path: `${RouteMedia}/:${RouteParamMediaId}`, canActivate: [authGuard], loadChildren: () => import('./media/media-details/routes')},
  {path: RouteMovies, canActivate: [authGuard], loadChildren: () => import('./media/routes')},
  {path: RouteSeries, canActivate: [authGuard], loadChildren: () => import('./media/routes')},
  {path: RouteTasks, canActivate: [authGuard], loadChildren: () => import('./tasks/routes')},
  {path: RouteActivity, canActivate: [authGuard], loadChildren: () => import('./activity/routes')},
  // Redirect old bookmarks to new Activity section
  {path: RouteLogs, redirectTo: `/${RouteActivity}/${RouteLogs}`, pathMatch: 'full'},
  {path: RouteEvents, redirectTo: `/${RouteActivity}/${RouteEvents}`, pathMatch: 'full'},
  {path: RouteSettings, canActivate: [authGuard], loadChildren: () => import('./settings/routes')},
  {path: '', redirectTo: RouteHome, pathMatch: 'full'},
  {path: '**', redirectTo: ''},
];

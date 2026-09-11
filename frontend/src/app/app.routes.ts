import {Routes} from '@angular/router';
import {RouteEvents, RouteHome, RouteLogs, RouteMedia, RouteMovies, RouteParamMediaId, RouteSeries, RouteSettings, RouteSetup, RouteTasks} from '../routing';
import {authGuard} from './auth/auth.guard';
import {setupOnlyWhenNeededGuard, setupRedirectGuard} from './setup/setup.guard';
import {LoginComponent} from './auth/login/login.component';

export const routes: Routes = [
  {path: 'login', component: LoginComponent},
  {path: RouteMedia, redirectTo: RouteHome, pathMatch: 'full'},
  {path: RouteSetup, canActivate: [authGuard, setupOnlyWhenNeededGuard], loadComponent: () => import('./setup/setup.component').then((m) => m.SetupComponent)},
  {path: RouteHome, canActivate: [authGuard, setupRedirectGuard], loadChildren: () => import('./media/routes')},
  {path: `${RouteMedia}/:${RouteParamMediaId}`, canActivate: [authGuard], loadChildren: () => import('./media/media-details/routes')},
  {path: RouteMovies, canActivate: [authGuard], loadChildren: () => import('./media/routes')},
  {path: RouteSeries, canActivate: [authGuard], loadChildren: () => import('./media/routes')},
  {path: RouteTasks, canActivate: [authGuard], loadChildren: () => import('./tasks/routes')},
  {path: RouteLogs, canActivate: [authGuard], loadChildren: () => import('./logs/routes')},
  {path: RouteEvents, canActivate: [authGuard], loadChildren: () => import('./events/routes')},
  {path: RouteSettings, canActivate: [authGuard], loadChildren: () => import('./settings/routes')},
  {path: '', redirectTo: RouteHome, pathMatch: 'full'},
  {path: '**', redirectTo: ''},
];

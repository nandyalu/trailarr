import {Routes} from '@angular/router';
import {RouteHome, RouteLogs, RouteMedia, RouteMovies, RouteParamMediaId, RouteSeries, RouteSettings, RouteTasks} from '../routing';

export const routes: Routes = [
  {path: RouteMedia, redirectTo: RouteHome, pathMatch: 'full'},
  {path: RouteHome, loadChildren: () => import('./media/routes')},
  {path: `${RouteMedia}/:${RouteParamMediaId}`, loadChildren: () => import('./media/media-details/routes')},
  {path: RouteMovies, loadChildren: () => import('./media/routes')},
  {path: RouteSeries, loadChildren: () => import('./media/routes')},
  // {path: 'series/:id', loadChildren: () => import('./media/media-details/routes')},
  {path: RouteTasks, loadChildren: () => import('./tasks/routes')},
  {path: RouteLogs, loadChildren: () => import('./logs/routes')},
  {path: RouteSettings, loadChildren: () => import('./settings/routes')},
  {path: '', redirectTo: RouteHome, pathMatch: 'full'},
  {path: '**', redirectTo: ''},
];

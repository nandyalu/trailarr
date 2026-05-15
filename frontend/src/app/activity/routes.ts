import {Route} from '@angular/router';
import {ActivityComponent} from './activity.component';
import {RouteEvents, RouteIssues, RouteLogs} from 'src/routing';

export default [
  {
    path: '',
    component: ActivityComponent,
    children: [
      {path: RouteIssues, loadComponent: () => import('./issues/issues.component').then((m) => m.IssuesComponent)},
      {path: RouteEvents, loadChildren: () => import('../events/routes')},
      {path: RouteLogs, loadChildren: () => import('../logs/routes')},
      {path: '', redirectTo: RouteIssues, pathMatch: 'full'},
    ],
  },
] as Route[];

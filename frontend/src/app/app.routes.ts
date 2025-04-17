import {Routes} from '@angular/router';
import {LogsComponent} from './logs/logs.component';
import {MediaComponent} from './media/media.component';
import {TasksComponent} from './tasks/tasks.component';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full',
  },
  {
    path: 'media',
    redirectTo: 'home',
    pathMatch: 'full',
  },
  {
    path: 'home',
    component: MediaComponent,
  },
  {
    path: 'media/:mediaId',
    loadChildren: () => import('./media/media-details/media-details.routes').then((m) => m.mediaDetailsRoutes),
  },
  {
    path: 'movies',
    component: MediaComponent,
  },
  {
    path: 'series',
    component: MediaComponent,
  },
  // {
  //     path: 'series/:id',
  //     component: MediaDetailsComponent
  // },
  {
    path: 'tasks',
    component: TasksComponent,
  },
  {
    path: 'logs',
    component: LogsComponent,
  },
  {
    path: 'settings',
    loadChildren: () => import('./settings/settings.routes').then((m) => m.settingsRoutes),
  },
];

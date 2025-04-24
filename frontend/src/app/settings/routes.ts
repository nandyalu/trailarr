import { Route } from '@angular/router';
import { RouteAbout, RouteAdd, RouteConnections, RouteEdit, RouteParamConnectionId, RouteTrailer } from 'src/routing';
import { AboutComponent } from './about/about.component';
import { AddConnectionComponent } from './connections/add-connection/add-connection.component';
import { ConnectionsComponent } from './connections/connections.component';
import { EditConnectionComponent } from './connections/edit-connection/edit-connection.component';
import { ShowConnectionsComponent } from './connections/show-connections/show-connections.component';
import { SettingsComponent } from './settings.component';
import { TrailerComponent } from './trailer/trailer.component';

export default [
  {
    path: '',
    loadComponent: () => SettingsComponent,
    children: [
      {
        path: RouteConnections,
        component: ConnectionsComponent,
        children: [
          {path: RouteAdd, component: AddConnectionComponent},
          {path: `${RouteEdit}/:${RouteParamConnectionId}`, component: EditConnectionComponent},
          {path: '', component: ShowConnectionsComponent},
        ],
      },
      {path: RouteTrailer, component: TrailerComponent},
      {path: RouteAbout, component: AboutComponent},
      {path: '**', redirectTo: RouteTrailer, pathMatch: 'prefix'},
    ],
  },
] as Route[];

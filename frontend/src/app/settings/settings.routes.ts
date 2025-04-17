import {Routes} from '@angular/router';
import {AboutComponent} from './about/about.component';
import {AddConnectionComponent} from './connections/add-connection/add-connection.component';
import {ConnectionsComponent} from './connections/connections.component';
import {EditConnectionComponent} from './connections/edit-connection/edit-connection.component';
import {ShowConnectionsComponent} from './connections/show-connections/show-connections.component';
import {SettingsComponent} from './settings.component';
import {TrailerComponent} from './trailer/trailer.component';

export const settingsRoutes: Routes = [
  {
    path: '',
    component: SettingsComponent,
    children: [
      {path: '', redirectTo: 'trailer', pathMatch: 'full'},
      {
        path: 'connections',
        component: ConnectionsComponent,
        children: [
          {path: '', component: ShowConnectionsComponent},
          {path: 'add', component: AddConnectionComponent},
          {path: 'edit/:id', component: EditConnectionComponent},
        ],
      },
      {path: 'trailer', component: TrailerComponent},
      {path: 'about', component: AboutComponent},
    ],
  },
];

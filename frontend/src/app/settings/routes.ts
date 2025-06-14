import {Route} from '@angular/router';
import {
  RouteAbout,
  RouteAdd,
  RouteConnections,
  RouteEdit,
  RouteGeneral,
  RouteParamConnectionId,
  RouteParamProfileId,
  RouteProfiles,
} from 'src/routing';
import {AboutComponent} from './about/about.component';
import {AddConnectionComponent} from './connections/add-connection/add-connection.component';
import {EditConnectionComponent} from './connections/edit-connection/edit-connection.component';
import {ShowConnectionsComponent} from './connections/show-connections/show-connections.component';
import {GeneralComponent} from './general/general.component';
import {EditProfileComponent} from './profiles/edit-profile/edit-profile.component';
import {ShowProfilesComponent} from './profiles/show-profiles/show-profiles.component';
import {SettingsComponent} from './settings.component';

export default [
  {
    path: '',
    loadComponent: () => SettingsComponent,
    children: [
      {path: RouteConnections, component: ShowConnectionsComponent},
      {path: `${RouteConnections}/${RouteAdd}`, component: AddConnectionComponent},
      {path: `${RouteConnections}/${RouteEdit}/:${RouteParamConnectionId}`, component: EditConnectionComponent},
      {path: RouteProfiles, component: ShowProfilesComponent},
      {path: `${RouteProfiles}/${RouteEdit}/:${RouteParamProfileId}`, component: EditProfileComponent},
      {path: RouteGeneral, component: GeneralComponent},
      {path: RouteAbout, component: AboutComponent},
      {path: '**', redirectTo: RouteGeneral, pathMatch: 'prefix'},
    ],
  },
] as Route[];

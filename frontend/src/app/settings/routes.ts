import {Route} from '@angular/router';
import {
  RouteAbout,
  RouteAdd,
  RouteConnections,
  RouteGeneral,
  RouteParamConnectionId,
  RouteParamProfileId,
  RouteProfiles,
} from 'src/routing';
import {AboutComponent} from './about/about.component';
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
      {path: `${RouteConnections}/${RouteAdd}`, component: EditConnectionComponent},
      {path: `${RouteConnections}/:${RouteParamConnectionId}`, component: EditConnectionComponent},
      {path: RouteProfiles, component: ShowProfilesComponent},
      {path: `${RouteProfiles}/:${RouteParamProfileId}`, component: EditProfileComponent},
      {path: RouteGeneral, component: GeneralComponent},
      {path: RouteAbout, component: AboutComponent},
      {path: '**', redirectTo: RouteGeneral, pathMatch: 'prefix'},
    ],
  },
] as Route[];

import {Route} from '@angular/router';
import {
  RouteAbout,
  RouteAdd,
  RouteConnections,
  RouteEdit,
  RouteParamConnectionId,
  RouteParamProfileId,
  RouteProfiles,
  RouteTrailer,
} from 'src/routing';
import {AboutComponent} from './about/about.component';
import {AddConnectionComponent} from './connections/add-connection/add-connection.component';
import {EditConnectionComponent} from './connections/edit-connection/edit-connection.component';
import {ShowConnectionsComponent} from './connections/show-connections/show-connections.component';
import {AddProfileComponent} from './profiles/add-profile/add-profile.component';
import {EditProfileComponent} from './profiles/edit-profile/edit-profile.component';
import {ShowProfilesComponent} from './profiles/show-profiles/show-profiles.component';
import {SettingsComponent} from './settings.component';
import {TrailerComponent} from './trailer/trailer.component';

export default [
  {
    path: '',
    loadComponent: () => SettingsComponent,
    children: [
      {path: RouteConnections, component: ShowConnectionsComponent},
      {path: `${RouteConnections}/${RouteAdd}`, component: AddConnectionComponent},
      {path: `${RouteConnections}/${RouteEdit}/:${RouteParamConnectionId}`, component: EditConnectionComponent},
      {path: RouteProfiles, component: ShowProfilesComponent},
      {path: `${RouteProfiles}/${RouteAdd}`, component: AddProfileComponent},
      {path: `${RouteProfiles}/${RouteEdit}/:${RouteParamProfileId}`, component: EditProfileComponent},
      {path: RouteTrailer, component: TrailerComponent},
      {path: RouteAbout, component: AboutComponent},
      {path: '**', redirectTo: RouteTrailer, pathMatch: 'prefix'},
    ],
  },
] as Route[];

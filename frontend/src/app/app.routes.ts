import { Routes } from '@angular/router';
import { HomeComponent } from './home/home.component';
import { LogsComponent } from './logs/logs.component';
import { MediaDetailsComponent } from './media/media-details/media-details.component';
import { MediaComponent } from './media/media.component';
import { AboutComponent } from './settings/about/about.component';
import { AddConnectionComponent } from './settings/connections/add-connection/add-connection.component';
import { ConnectionsComponent } from './settings/connections/connections.component';
import { EditConnectionComponent } from './settings/connections/edit-connection/edit-connection.component';
import { ShowConnectionsComponent } from './settings/connections/show-connections/show-connections.component';
import { SettingsComponent } from './settings/settings.component';
import { TrailerComponent } from './settings/trailer/trailer.component';
import { TasksComponent } from './tasks/tasks.component';

export const routes: Routes = [
    {
        path: '',
        redirectTo: 'home',
        pathMatch: 'full'
    },
    {
        path: 'media',
        redirectTo: 'home',
        pathMatch: 'full'
    },
    {
        path: 'home',
        component: HomeComponent
    },
    {
        path: 'media/:id',
        component: MediaDetailsComponent
    },
    {
        path: 'movies',
        component: MediaComponent
    },
    {
        path: 'series',
        component: MediaComponent
    },
    // {
    //     path: 'series/:id',
    //     component: MediaDetailsComponent
    // },
    {
        path: 'tasks',
        component: TasksComponent
    },
    {
        path: 'logs',
        component: LogsComponent
    },
    {
        path: 'settings',
        component: SettingsComponent, 
        children: [
            { path: '', redirectTo: 'trailer', pathMatch: 'full' },
            {
                path: 'connections',
                component: ConnectionsComponent,
                children: [
                    { path: '', component: ShowConnectionsComponent },
                    { path: 'add', component: AddConnectionComponent },
                    { path: 'edit/:id', component: EditConnectionComponent }
                ]
            },
            { path: 'trailer', component: TrailerComponent },
            { path: 'about', component: AboutComponent }
        ]
     }

];

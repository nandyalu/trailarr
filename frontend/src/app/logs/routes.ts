import {Route} from '@angular/router';
import {LogsComponent} from './logs.component';

export default [{path: '', loadComponent: () => LogsComponent}] as Route[];

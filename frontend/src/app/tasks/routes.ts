import {Route} from '@angular/router';
import {TasksComponent} from './tasks.component';

export default [{path: '', loadComponent: () => TasksComponent}] as Route[];

import {Route} from '@angular/router';
import {MediaComponent} from './media.component';

export default [{path: '', loadComponent: () => MediaComponent}] as Route[];

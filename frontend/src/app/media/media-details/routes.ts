import {Route} from '@angular/router';
import {MediaDetailsComponent} from './media-details.component';

export default [{path: '', loadComponent: () => MediaDetailsComponent}] as Route[];

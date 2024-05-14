import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterOutlet } from '@angular/router';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { MoviesComponent } from "../frontend/src/app/movies/movies.component";
import { SidenavComponent } from "./nav/sidenav/sidenav.component";
import { TopnavComponent } from "./nav/topnav/topnav.component";
import { NavbarComponent } from './navbar/navbar.component';

@Component({
    selector: 'app-root',
    standalone: true,
    templateUrl: './app.component.html',
    styleUrl: './app.component.css',
    imports: [NgbModule, RouterOutlet, MoviesComponent, FormsModule, NavbarComponent, TopnavComponent, SidenavComponent]
})
export class AppComponent {
  title = 'Trailarr';
}
 
import { HttpClientModule } from '@angular/common/http';
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { MoviesComponent } from './movies/movies.component';
import { SidenavComponent } from './nav/sidenav/sidenav.component';
import { TopnavComponent } from './nav/topnav/topnav.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, TopnavComponent, SidenavComponent, MoviesComponent, HttpClientModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'Trailarr';
}

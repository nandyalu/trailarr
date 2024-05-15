import { NgFor, NgIf, UpperCasePipe } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Media } from '../models/media';
import { MovieService } from '../services/movie.service';

@Component({
  selector: 'app-movies',
  standalone: true,
  imports: [UpperCasePipe, FormsModule, NgIf, NgFor],
  templateUrl: './movies.component.html',
  styleUrl: './movies.component.css'
})
export class MoviesComponent {
  
  title = 'Movies';
  movies: Media[] = [];
  isLoading = true;

  constructor(private movieService: MovieService) { }
  
  ngOnInit(): void {
    this.isLoading = true;
    this.movieService.getMovies().subscribe((movies: Media[]) => {
      this.movies = movies;
      this.isLoading = false;
    });
  }
}

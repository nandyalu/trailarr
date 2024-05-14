import { NgFor, NgIf, UpperCasePipe } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Movie } from '../models/movie';
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
  movies: Movie[] = [];
  isLoading = true;

  constructor(private movieService: MovieService) { }
  
  ngOnInit(): void {
    this.isLoading = true;
    this.movieService.getMovies().subscribe((movies: Movie[]) => {
      this.movies = movies;
      this.isLoading = false;
    });
  }
}

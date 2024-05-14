import { NgFor, NgIf, UpperCasePipe } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Movie } from '../models/movie';
import { MovieService } from '../services/movie.service';

@Component({
  selector: 'app-series',
  standalone: true,
  imports: [UpperCasePipe, FormsModule, NgIf, NgFor],
  templateUrl: './series.component.html',
  styleUrl: './series.component.css'
})
export class SeriesComponent {
  title = 'Series';
  series: Movie[] = [];
  isLoading = true;

  constructor(private movieService: MovieService) { }
  
  ngOnInit(): void {
    this.isLoading = true;
    this.movieService.getMovies().subscribe((movies: Movie[]) => {
      this.series = movies;
      this.isLoading = false;
    });
  }
}

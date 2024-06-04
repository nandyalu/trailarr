import { NgFor, NgIf, UpperCasePipe } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Media } from '../models/media';
import { MovieService } from '../services/movie.service';
import { SeriesService } from '../services/series.service';

@Component({
  selector: 'app-media',
  standalone: true,
  imports: [UpperCasePipe, FormsModule, NgIf, NgFor, RouterLink],
  templateUrl: './media.component.html',
  styleUrl: './media.component.css'
})
export class MediaComponent {
  title = 'Media';
  media_list: Media[] = [];
  isLoading = true;
  mediaService: MovieService | SeriesService = this.seriesService;

  constructor(
    private movieService: MovieService,
    private seriesService: SeriesService,
    private route: ActivatedRoute
  ) { }
  
  ngOnInit(): void {
    this.isLoading = true;
    let type = this.route.snapshot.url[0].path;
    if (type === 'movies') {
      this.title = 'Movies';
      this.mediaService = this.movieService;
    } else {
      this.title = 'Series';
      this.mediaService = this.seriesService;
    }
    this.mediaService.getRecentMedia().subscribe((media_list: Media[]) => {
      this.media_list = media_list;
      this.isLoading = false;
    });
  }
 
}

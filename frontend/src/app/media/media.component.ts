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
  allMedia: Media[] = [];
  isLoading = true;
  selectedSort = 'added_at';
  sortAscending = true;
  sortOptions: (keyof Media)[] = ['title', 'year', 'added_at', 'updated_at'];
  selectedFilter = 'all';
  filterOptions: string[] = ['all', 'monitored', 'unmonitored', 'downloaded', 'missing'];
  private mediaService: MovieService | SeriesService = this.seriesService;

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
      this.mediaService.getAllMedia().subscribe((media_list: Media[]) => {
        this.displayMedia(media_list);
      });
    } else if (type === 'series') {
      this.title = 'Series';
      this.mediaService = this.seriesService;
      this.mediaService.getRecentMedia().subscribe((media_list: Media[]) => {
        this.displayMedia(media_list);
      });
    } else {
      this.title = 'All Media';
      this.mediaService = this.movieService;
      this.mediaService.getAllMedia().subscribe((media_list: Media[]) => {
        this.displayMedia(media_list);
      });
    }
    
  }
 
  displayMedia(media_list: Media[]): void {
    this.media_list = [];
    this.allMedia = media_list;
    debugger;
    let filteredMedia = this.filterMediaList(this.selectedFilter);
    this.isLoading = false;
    filteredMedia.forEach((media, index) => {
      if (index > 60) {
        setTimeout(() => {
          this.media_list.push(media);
        }, 61 * 20); // 20 milliseconds delay for each item
      } else {
        setTimeout(() => {
          this.media_list.push(media);
        }, index * 20); // 20 milliseconds delay for each item
      }
    });
  }

  displayOptionTitle(option: string): string {
    option = option.replace('_at', '');
    return option.charAt(0).toUpperCase() + option.slice(1);
  }

  sortMediaList(sortBy: keyof Media): void {
    if (this.selectedSort === sortBy) {
      this.media_list.reverse();
      this.sortAscending = !this.sortAscending;
      return;
    }
    this.selectedSort = sortBy;
    this.sortAscending = true;
    this.media_list.sort((a, b) => (a[sortBy].toString().localeCompare(b[sortBy].toString())));
  }

  setMediaFilter(filterBy: string): void {
    this.selectedFilter = filterBy;
    this.displayMedia(this.allMedia);
    return;
  }

  filterMediaList(filterBy: string): Media[] {
    if (filterBy === 'all') {
      return this.allMedia;
    }
    if (filterBy === 'monitored') {
      return this.allMedia.filter((media) => media.monitor);
    }
    if (filterBy === 'unmonitored') {
      return this.allMedia.filter((media) => !media.monitor);
    }
    if (filterBy === 'downloaded') {
      return this.allMedia.filter((media) => media.downloaded_at !== null);
    }
    if (filterBy === 'missing') {
      return this.allMedia.filter((media) => media.downloaded_at === null);
    }
    // return this.allMedia.filter((media) => {
    //   if (filterBy === 'unmonitored') {
    //     return !media.monitor;
    //   } else if (filterBy === 'downloaded') {
    //     return media.downloaded_at;
    //   } else if (filterBy === 'missing') {
    //     return !media.downloaded_at;
    //   }
    //   return false;
    // });
    return this.allMedia;
  }
}

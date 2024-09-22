import { NgFor, NgIf, UpperCasePipe } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ScrollNearEndDirective } from '../helpers/scroll-near-end-directive';
import { Media } from '../models/media';
import { MovieService } from '../services/movie.service';
import { SeriesService } from '../services/series.service';

@Component({
  selector: 'app-media',
  standalone: true,
  imports: [UpperCasePipe, FormsModule, NgIf, NgFor, RouterLink, ScrollNearEndDirective],
  templateUrl: './media.component.html',
  styleUrl: './media.component.css'
})
export class MediaComponent {
  title = 'Media';
  pageType = 'Media';
  displayCount = 50;
  displayMediaList: Media[] = [];
  filteredMediaList: Media[] = [];
  allMedia: Media[] = [];
  isLoading = true;
  selectedSort: keyof Media = 'added_at';
  sortAscending = true;
  sortOptions: (keyof Media)[] = ['title', 'year', 'added_at', 'updated_at'];
  selectedFilter = 'missing';
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
      this.pageType = 'Movies';
      this.mediaService = this.movieService;
      this.mediaService.getAllMedia().subscribe((mediaList: Media[]) => {
        this.displayMedia(mediaList);
      });
    } else if (type === 'series') {
      this.title = 'Series';
      this.pageType = 'Series';
      this.mediaService = this.seriesService;
      this.mediaService.getAllMedia().subscribe((mediaList: Media[]) => {
        this.displayMedia(mediaList);
      });
    } else {
      this.title = 'All Media';
      this.pageType = 'AllMedia';
      this.mediaService = this.movieService;
      this.mediaService.getAllMedia().subscribe((mediaList: Media[]) => {
        this.displayMedia(mediaList);
      });
    }
  }

  saveSortOption(): void {
    // Save the sort option to the local session
    localStorage.setItem(`Trailarr${this.pageType}Sort`, this.selectedSort);
    localStorage.setItem(`Trailarr${this.pageType}SortAscending`, this.sortAscending.toString());
  }

  saveFilterOption(): void {
    // Save the filter option to the local session
    localStorage.setItem(`Trailarr${this.pageType}Filter`, this.selectedFilter);
  }

  retrieveSortOption(): void {
    // Retrieve the sort option from the local session
    let sortOption = localStorage.getItem(`Trailarr${this.pageType}Sort`);
    let sortAscending = localStorage.getItem(`Trailarr${this.pageType}SortAscending`);
    if (sortOption) {
      this.selectedSort = sortOption as keyof Media;
    }
    if (sortAscending) {
      this.sortAscending = sortAscending === 'true';
    }
  }

  retrieveFilterOption(): void {
    // Retrieve the filter option from the local session
    let filterOption = localStorage.getItem(`Trailarr${this.pageType}Filter`);
    if (filterOption) {
      this.selectedFilter = filterOption;
    }
  }

  displayMedia(mediaList: Media[]): void {
    this.retrieveSortOption();
    this.retrieveFilterOption();
    this.displayMediaList = [];
    this.displayCount = 50;
    this.allMedia = mediaList;
    // debugger;
    this.filteredMediaList = this.filterMediaList(this.selectedFilter, mediaList);
    this.sortMediaList(this.selectedSort, this.filteredMediaList);
    this.isLoading = false;
    this.displayMediaList = this.filteredMediaList.slice(0, this.displayCount);
    // this.filteredMediaList.forEach((media, index) => {
    //   if (index < this.displayCount) {
    //     this.displayMediaList.push(media);
    //   }
    //   // this.displayMediaList.push(media);
    //   // if (index > 60) {
    //   //   setTimeout(() => {
    //   //     this.displayMediaList.push(media);
    //   //   }, 61 * 20); // 20 milliseconds delay for each item
    //   // } else {
    //   //   setTimeout(() => {
    //   //     this.displayMediaList.push(media);
    //   //   }, index * 20); // 20 milliseconds delay for each item
    //   // }
    // });
  }

  displayOptionTitle(option: string): string {
    option = option.replace('_at', '');
    return option.charAt(0).toUpperCase() + option.slice(1);
  }

  sortMediaList(sortBy: keyof Media, mediaList: Media[]): void {
    // Sort the media list by the selected sort option
    // Sorts the list in place. If sortAscending is false, reverses the list
    mediaList.sort((a, b) => (a[sortBy].toString().localeCompare(b[sortBy].toString())));
    if (!this.sortAscending) {
      mediaList.reverse();
    }
  }

  setMediaSort(sortBy: keyof Media): void {
    this.displayCount = 50;
    if (this.selectedSort === sortBy) {
      this.sortAscending = !this.sortAscending;
    } else {
      this.selectedSort = sortBy;
      this.sortAscending = true;
    }
    this.sortMediaList(sortBy, this.filteredMediaList);
    this.displayMediaList = this.filteredMediaList.slice(0, this.displayCount);
    this.saveSortOption();
    return;
  }

  setMediaFilter(filterBy: string): void {
    this.isLoading = true;
    this.displayCount = 50;
    this.displayMediaList = [];
    this.filteredMediaList = [];
    this.selectedFilter = filterBy;
    this.filteredMediaList = this.filterMediaList(filterBy, this.allMedia);
    this.sortMediaList(this.selectedSort, this.filteredMediaList);
    setTimeout(() => {
      this.isLoading = false;
      this.displayMediaList = this.filteredMediaList.slice(0, this.displayCount);
    }, 1000);
    this.saveFilterOption();
    return;
  }

  filterMediaList(filterBy: string, mediaList: Media[]): Media[] {
    if (mediaList.length === 0) {
      return mediaList;
    }
    if (filterBy === 'all') {
      return mediaList;
    }
    if (filterBy === 'monitored') {
      return mediaList.filter((media) => media.monitor);
    }
    if (filterBy === 'unmonitored') {
      return mediaList.filter((media) => !media.monitor && !media.trailer_exists);
    }
    if (filterBy === 'downloaded') {
      return mediaList.filter((media) => media.trailer_exists);
    }
    if (filterBy === 'missing') {
      return mediaList.filter((media) => !media.trailer_exists);
    }
    return mediaList;
  }

  onNearEndScroll(): void {
    // Load more media when near the end of the scroll
    // console.log('Near end of scroll');
    if (this.displayCount >= this.filteredMediaList.length) {
      return;
    }
    this.displayMediaList.push(
      ...this.filteredMediaList.slice(this.displayCount, this.displayCount + 20)
    );
    this.displayCount += 20;
  }
}

import { NgFor, NgIf } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom, Observable } from 'rxjs';
import { ScrollNearEndDirective } from '../helpers/scroll-near-end-directive';
import { Media } from '../models/media';
import { MediaService } from '../services/media.service';

@Component({
    selector: 'app-media',
    imports: [FormsModule, NgIf, NgFor, RouterLink, ScrollNearEndDirective],
    templateUrl: './media.component.html',
    styleUrl: './media.component.css'
})
export class MediaComponent {
  title = 'Media';
  pageType = 'Media';
  moviesOnly: boolean | null = true;
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
  filteredMediaMap: { [key: string]: Media[] } = {};
  monitoredMedia: Media[] = [];
  unmonitoredMedia: Media[] = [];
  downloadedMedia: Media[] = [];
  missingMedia: Media[] = [];

  constructor(
    private mediaService: MediaService,
    private route: ActivatedRoute
  ) { }

  ngOnInit(): void {
    this.isLoading = true;
    let type = this.route.snapshot.url[0].path;
    if (type === 'movies') {
      this.title = 'Movies';
      this.pageType = 'Movies';
      this.moviesOnly = true;
    } else if (type === 'series') {
      this.title = 'Series';
      this.pageType = 'Series';
      this.moviesOnly = false;
    } else {
      this.title = 'All Media';
      this.pageType = 'AllMedia';
      this.moviesOnly = null;
    }
    this.retrieveFilterOption();
    this.retrieveSortOption();
    this.getAndDisplayMedia();
  }

  /**
   *  Get and display media
   * - Gets the selected sort and filter options media list first and displays it
   * - Gets the rest of the filter options media lists and stores them in the filteredMediaMap
   */
  async getAndDisplayMedia(): Promise<void> {
    // Get the selected sort and filter options media list first and display it
    let selectedFilterMediaList = this.filteredMediaMap[this.selectedFilter];
    if (!selectedFilterMediaList) {
      selectedFilterMediaList = await this.getFilteredMedia(this.selectedFilter);
      this.filteredMediaMap[this.selectedFilter] = selectedFilterMediaList;
      this.displayMedia();
    } else {
      this.displayMedia();
    }

    // Get the rest of the filter options media lists
    for (let filter of this.filterOptions) {
      if (filter === this.selectedFilter) {
        continue;
      }
      let filterMediaList = this.filteredMediaMap[filter];
      if (!filterMediaList) {
        filterMediaList = await this.getFilteredMedia(filter);
        this.filteredMediaMap[filter] = filterMediaList;
      }
    }
  }

  /**
   * Retrieves a filtered list of media items based on the provided filter criteria.
   *
   * @param filterBy - The criteria to filter the media items by. 
   * - Can be `all`, `downloaded`, `monitored`, `unmonitored`, or `missing`.
   * @returns An array of filtered media items.
   */
  async getFilteredMedia(filterBy: string): Promise<Media[]> {
    const mediaObservable: Observable<Media[]> = this.mediaService.getAllMedia(
      this.moviesOnly,
      filterBy,
      this.selectedSort.toString(),
      this.sortAscending
    );
    const mediaList = await firstValueFrom(mediaObservable);
    return mediaList;
  }

  /**
   * Saves the current sort option and sort order to the local storage.
   * The sort option is saved with a key that includes the page type.
   * The sort order (ascending or descending) is also saved as a string.
   *
   * @remarks
   * This method uses `localStorage` to persist the sort option and order.
   * The keys used for storage are dynamically generated based on the `pageType`.
   *
   * @example
   * // Assuming `pageType` is 'Movies' and `selectedSort` is 'Title':
   * saveSortOption();
   * // This will store the following in localStorage:
   * // Key: 'TrailarrMoviesSort', Value: 'Title'
   * // Key: 'TrailarrMoviesSortAscending', Value: 'true' or 'false'
   */
  saveSortOption(): void {
    // Save the sort option to the local session
    localStorage.setItem(`Trailarr${this.pageType}Sort`, this.selectedSort);
    localStorage.setItem(`Trailarr${this.pageType}SortAscending`, this.sortAscending.toString());
  }

  /**
   * Saves the currently selected filter option to the local storage.
   * The filter option is stored with a key that combines a prefix 'Trailarr'
   * and the current page type.
   *
   * @remarks
   * This method uses the `localStorage` API to persist the filter option
   * across sessions.
   *
   * @example
   * // If the `pageType` is 'Movies' and the `selectedFilter` is 'Genre',
   * // the filter option will be saved with the key 'TrailarrMoviesFilter'.
   */
  saveFilterOption(): void {
    // Save the filter option to the local session
    localStorage.setItem(`Trailarr${this.pageType}Filter`, this.selectedFilter);
  }

  /**
   * Retrieves the sort option and sort order from the local storage.
   * 
   * This method fetches the sort option and sort order for the current page type
   * from the local storage. It updates the `selectedSort` and `sortAscending` 
   * properties of the component based on the retrieved values.
   * 
   * - The sort option is stored with the key `Trailarr{pageType}Sort`.
   * - The sort order is stored with the key `Trailarr{pageType}SortAscending`.
   * 
   * If the sort option is found, it is cast to a key of the `Media` type and 
   * assigned to `selectedSort`. 
   * If the sort order is found, it is converted to 
   * a boolean and assigned to `sortAscending`.
   * 
   * @returns {void}
   */
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

  /**
   * Retrieves the filter option from the local storage for the current page type.
   * If a filter option is found, it sets the `selectedFilter` property to the retrieved value.
   * The filter option is stored in local storage with a key in the format `Trailarr{pageType}Filter`.
   */
  retrieveFilterOption(): void {
    // Retrieve the filter option from the local session
    let filterOption = localStorage.getItem(`Trailarr${this.pageType}Filter`);
    if (filterOption) {
      this.selectedFilter = filterOption;
    }
  }

  /**
   * Displays the media items based on the selected filter and sort options.
   * 
   * This method performs the following actions:
   * 1. Shows a loading screen.
   * 2. Clears the current display and filtered media lists.
   * 3. Sets the initial display count to 50.
   * 4. Retrieves the media list based on the selected filter.
   * 5. Sorts the filtered media list based on the selected sort option.
   * 6. After a delay to avoid flickering, hides the loading screen and displays the first 50 items from the sorted media list.
   * 
   * @returns {void}
   */
  displayMedia(): void {
    // Show loading screen
    this.isLoading = true;
    // Clear the display and filtered media lists
    this.displayMediaList = [];
    this.filteredMediaList = [];
    this.displayCount = 50;
    // debugger;
    // Get the selected filter media list
    this.filteredMediaList = this.filteredMediaMap[this.selectedFilter];
    // Sort the selected filter media list
    this.sortMediaList(this.selectedSort, this.filteredMediaList);
    setTimeout(() => {
      // Clear the loading screen and display the media list [first 50 items]
      // Added a delay to avoid flickering
      this.isLoading = false;
      this.displayMediaList = this.filteredMediaList.slice(0, this.displayCount);
    }, 1000);
  }

  /**
   * Formats the given option string by removing the substring '_at' and capitalizing the first letter.
   *
   * @param option - The option string to be formatted.
   * @returns The formatted option string with '_at' removed and the first letter capitalized.
   */
  displayOptionTitle(option: string): string {
    option = option.replace('_at', '');
    return option.charAt(0).toUpperCase() + option.slice(1);
  }

  /**
   * Sorts the media list by the selected sort option.
   * 
   * @param sortBy - The key of the Media object to sort by.
   * @param mediaList - The list of Media objects to be sorted.
   * 
   * @remarks
   * This method sorts the media list in place. If `sortAscending` is false, 
   * the sorted list will be reversed.
   */
  sortMediaList(sortBy: keyof Media, mediaList: Media[]): void {
    // Sort the media list by the selected sort option
    // Sorts the list in place. If sortAscending is false, reverses the list
    mediaList.sort((a, b) => (a[sortBy].toString().localeCompare(b[sortBy].toString())));
    if (!this.sortAscending) {
      mediaList.reverse();
    }
  }

  /**
   * Sets the sorting criteria for the media list.
   * 
   * This method updates the sorting criteria based on the provided key. If the 
   * provided key is the same as the current sorting key, it toggles the sorting 
   * order between ascending and descending. If the provided key is different, 
   * it sets the sorting order to ascending. It then sorts the media list 
   * accordingly, updates the display list to show the top 50 items, and saves 
   * the sorting option.
   * 
   * @param sortBy - The key of the Media object to sort by.
   * @returns void
   */
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

  /**
   * Sets the media filter based on the provided filter string.
   * Updates the selected filter, displays the media according to the new filter,
   * and saves the filter option.
   *
   * @param filterBy - The filter string to set for media filtering.
   * @returns void
   */
  setMediaFilter(filterBy: string): void {
    this.selectedFilter = filterBy;
    this.displayMedia();
    this.saveFilterOption();
    return;
  }

  /**
   * Handles the event when the user scrolls near the end of the media list.
   * Loads more media items into the display list if there are more items to show.
   * 
   * @returns {void} This method does not return a value.
   */
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

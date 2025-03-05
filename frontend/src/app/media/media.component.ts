import { NgTemplateOutlet } from '@angular/common';
import { Component, computed, ElementRef, signal, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ScrollNearEndDirective } from '../helpers/scroll-near-end-directive';
import { mapMedia, Media } from '../models/media';
import { MediaService } from '../services/media.service';
import { WebsocketService } from '../services/websocket.service';
import { AddCustomFilterDialogComponent } from "./add-filter-dialog/add-filter-dialog.component";

@Component({
  selector: 'app-media2',
  imports: [FormsModule, NgTemplateOutlet, RouterLink, ScrollNearEndDirective, AddCustomFilterDialogComponent],
  templateUrl: './media.component.html',
  styleUrl: './media.component.css'
})
export class MediaComponent {

  constructor(
    private route: ActivatedRoute,
    private mediaService: MediaService,
    private webSocketService: WebsocketService
  ) { }

  moviesOnly = signal<boolean | null>(null);
  isLoading = signal<boolean>(true);

  inEditMode: boolean = false;
  selectedMedia: number[] = [];

  sortOptions: (keyof Media)[] = ['title', 'year', 'added_at', 'updated_at'];
  filterOptions: string[] = ['all', 'downloaded', 'downloading', 'missing', 'monitored', 'unmonitored'];
  selectedSort = signal<keyof Media>('added_at');
  sortAscending = signal<boolean>(true);
  selectedFilter = signal<string>('all');

  defaultDisplayCount = 50;
  displayCount = signal<number>(this.defaultDisplayCount);

  allMedia = signal<Media[]>([]);
  filteredSortedMedia = computed(() => this.computeFilteredNSortedMedia());
  displayMedia = computed(() => {
    // console.log("C: Displaying media");
    return this.filteredSortedMedia().slice(0, this.displayCount())
  });
  isCustomFilterDialogOpen = false;

  private lastUpdateTime: number = 0;
  private readonly UPDATE_INTERVAL: number = 3; // 3 seconds in seconds

  ngOnInit(): void {
    this.isLoading.set(true);
    let type = this.route.snapshot.url[0].path;
    switch (type) {
      case 'movies':
        this.moviesOnly.set(true);
        break;
      case 'series':
        this.moviesOnly.set(false);
        break;
      default:
        this.moviesOnly.set(null);
        this.filterOptions = ['all', 'movies', 'series']
        this.selectedFilter.set('all');
        this.selectedSort.set('updated_at');
        this.sortAscending.set(false);
    }
    this.retrieveSortNFilterOptions();
    // this.mediaService.fetchAllMedia(this.moviesOnly());
    // Get all media for Movies or Series, downloaded only for Home
    let filterBy = this.moviesOnly() == null ? 'downloaded' : 'all';
    this.mediaService.fetchAllMedia(this.moviesOnly(), filterBy).subscribe(
      (mediaList) => {
        // console.log("C: Media fetched");
        this.allMedia.set(mediaList.map(media => mapMedia(media)));
        this.isLoading.set(false);
      }
    )

    // Subscribe to WebSocket updates
    this.webSocketService.toastMessage.subscribe(() => {
      this.fetchUpdatedMedia();
    });

    // Fetch updated media items every 10 seconds
    setTimeout(() => {
      this.fetchUpdatedMedia();
    }, 10000);
  }

  /**
   * Filters and sorts the media list based on the selected filter and sort options.
   * 
   * @returns {Media[]} The filtered and sorted media list.
   */
  computeFilteredNSortedMedia(): Media[] {
    // Filter the media list by the selected filter option
    this.lastUpdateTime = Date.now();
    let mediaList = this.allMedia().filter(media => {
      switch (this.selectedFilter()) {
        case 'all':
          return true;
        case 'downloaded':
          return media.trailer_exists;
        case 'downloading':
          return media.status.toLowerCase() === 'downloading';
        case 'missing':
          return !media.trailer_exists;
        case 'monitored':
          return media.monitor;
        case 'unmonitored':
          return !media.monitor && !media.trailer_exists;
        case 'movies':
          return media.is_movie && media.trailer_exists;
        case 'series':
          return !media.is_movie && media.trailer_exists;
        default:
          return true;
      }
    });
    // Sort the media list by the selected sort option
    // Sorts the list in place. If sortAscending is false, reverses the list
    mediaList.sort((a, b) => {
      let aVal = a[this.selectedSort()];
      let bVal = b[this.selectedSort()];
      if (aVal instanceof Date && bVal instanceof Date) {
        if (this.sortAscending()) {
          return aVal.getTime() - bVal.getTime();
        }
        return bVal.getTime() - aVal.getTime();
      }
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        if (this.sortAscending()) {
          return aVal - bVal;
        }
        return bVal - aVal;
      }
      if (this.sortAscending()) {
        return a[this.selectedSort()].toString().localeCompare(b[this.selectedSort()].toString());
      }
      return b[this.selectedSort()].toString().localeCompare(a[this.selectedSort()].toString());
    });
    return mediaList;
  }

  /**
   * Fetches updated media items from the server and updates the allMedia signal.
   * 
   * @param {boolean} forceUpdate - Whether to force an update regardless of 
   * the time interval.
   *
   * @returns {void}
   */
  fetchUpdatedMedia(forceUpdate: boolean = false): void {
    // Fetch updated media items from the server and update the allMedia signal
    const currentTime = Date.now();
    const delta = Math.floor(Math.abs(currentTime - this.lastUpdateTime) / 1000);
    if (delta > this.UPDATE_INTERVAL || forceUpdate) {
      // Fetch updated media items
      this.mediaService.fetchUpdatedMedia(delta).subscribe(
        (mediaList) => {
          let updatedMedia = mediaList.map(media => mapMedia(media));
          this.allMedia.update((existingMedia) => {
            return existingMedia.map(media => {
              let updated = updatedMedia.find(m => m.id === media.id);
              if (updated) {
                return updated;
              }
              return media;
            });
          });
        }
      );
      // this.mediaService.fetchAllMedia(this.moviesOnly());
      this.lastUpdateTime = currentTime;
    }
  }

  /**
   * Toggles the edit mode for the media list.
   * 
   * @param {boolean} enabled - Whether to enable or disable edit mode.
   * @returns {void}
   */
  toggleEditMode(enabled: boolean): void {
    this.inEditMode = enabled;
  }

  selectAll(): void {
    this.selectedMedia = this.filteredSortedMedia().map(media => media.id);
  }

  /**
   * Handles the event when a media item is selected, either by checking or unchecking a checkbox.
   * Adds or removes the media item from the selectedMedia array based on the checkbox state.
   * 
   * @param {Media} media - The media item that was selected.
   * @param {Event} event - The event that triggered the selection.
   * @returns {void}
   */
  onMediaSelected(media: Media, event: Event): void {
    // Navigate to the media details page
    const inputElement = event.target as HTMLInputElement;
    // console.log("Media selected:", media.id, "Checked:", inputElement.checked);
    if (inputElement.checked) {
      this.selectedMedia.push(media.id);
    } else {
      this.selectedMedia = this.selectedMedia.filter((id) => id !== media.id);
    }
  }

  /**
   * Handles the batch update action for the selected media items.
   * 
   * @param {string} action
   * The action to perform on the selected media items. Available actions are:
   * - `monitor`: Monitor the selected media items.
   * - `unmonitor`: Unmonitor the selected media items.
   * - `delete`: Delete the trailers for the selected media items.
   * - `download`: Download the trailers for the selected media items.
   * @returns {void}
   */
  batchUpdate(action: string): void {
    // console.log("Batch update:", action, "Selected media:", this.selectedMedia);
    this.webSocketService.showToast(`Batch update: ${action} ${this.selectedMedia.length} items`);
    this.mediaService.batchUpdate(this.selectedMedia, action).subscribe(() => {
      // console.log("C: Batch update successful");
      this.fetchUpdatedMedia(true); // Fetch updated media items
    });
    this.selectedMedia = [];
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
   * Retrieves the sort and filter options from the local session.
   * If no options are found, sets the default sort option to 'added_at' and the default filter option to 'all'.
   * 
   * - The sort option is stored with the key `Trailarr{pageType}Sort`.
   * - The sort order is stored with the key `Trailarr{pageType}SortAscending`.
   * - The filter option is stored with the key `Trailarr{pageType}Filter`.
   * 
   * @returns {void} This method does not return a value.
   */
  retrieveSortNFilterOptions(): void {
    const moviesOnlyValue = this.moviesOnly();
    const pageType = moviesOnlyValue == null ? 'AllMedia' : (moviesOnlyValue ? 'Movies' : 'Series');
    // Retrieve the filter option from the local session
    let filterOption = localStorage.getItem(`Trailarr${pageType}Filter`);
    if (filterOption) {
      this.selectedFilter.set(filterOption);
    }
    // Retrieve the sort option from the local session
    let sortOption = localStorage.getItem(`Trailarr${pageType}Sort`);
    let sortAscending = localStorage.getItem(`Trailarr${pageType}SortAscending`);
    if (sortOption) {
      this.selectedSort.set(sortOption as keyof Media);
    }
    if (sortAscending) {
      this.sortAscending.set(sortAscending == 'true');
    }
  }

  /**
   * Sets the media sort option and resets the display count to the default.
   * Also, saves the sort option to the local session.
   * If the same sort option is selected, toggles the sort direction.
   * 
   * @param sortBy - The sort option to set.
   * @returns {void} This method does not return a value.
  */
  setMediaSort(sortBy: keyof Media): void {
    this.selectedMedia = []; // Clear the selected media items
    this.displayCount.set(this.defaultDisplayCount); // Reset the display count to the default
    if (this.selectedSort() === sortBy) {
      // If the same sort option is selected, toggle the sort direction
      this.sortAscending.set(!this.sortAscending());
    } else {
      // If a new sort option is selected, set the sort option and direction
      this.selectedSort.set(sortBy);
      this.sortAscending.set(true);
    }
    // Save the sort option to the local session
    const moviesOnly = this.moviesOnly();
    const pageType = moviesOnly == null ? 'AllMedia' : (moviesOnly ? 'Movies' : 'Series');
    localStorage.setItem(`Trailarr${pageType}Sort`, this.selectedSort());
    localStorage.setItem(`Trailarr${pageType}SortAscending`, this.sortAscending().toString());
    return;
  }

  /**
   * Sets the media filter option and resets the display count to the default.
   * 
   * @param filterBy - The filter option to set.
   * @returns {void} This method does not return a value.
   */
  setMediaFilter(filterBy: string): void {
    this.selectedMedia = []; // Clear the selected media items
    // Reset the display count to the default
    this.displayCount.set(this.defaultDisplayCount);
    // Set the filter option
    this.selectedFilter.set(filterBy);
    // Save the filter option to the local session
    const moviesOnly = this.moviesOnly();
    const pageType = moviesOnly == null ? 'AllMedia' : (moviesOnly ? 'Movies' : 'Series');
    localStorage.setItem(`Trailarr${pageType}Filter`, this.selectedFilter());
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
    if (this.displayCount() >= this.filteredSortedMedia().length) {
      return;
    }
    this.displayCount.update((count) => count + this.defaultDisplayCount);
  }

  @ViewChild('addFilterDialog') addFilterDialog!: ElementRef<HTMLDialogElement>;
  openAddFilterDialog(): void {
    this.addFilterDialog.nativeElement.showModal();
    this.isCustomFilterDialogOpen = true;
  }

  closeAddFilterDialog(): void {
    this.addFilterDialog.nativeElement.close();
    // Delay closing the dialog to prevent content disappearing immediately
    setTimeout(() => {
      this.isCustomFilterDialogOpen = false;
    }, 1000);
  }


}

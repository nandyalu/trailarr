import { NgTemplateOutlet } from '@angular/common';
import { Component, computed, ElementRef, inject, signal, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ScrollNearEndDirective } from '../helpers/scroll-near-end-directive';
import { booleanFilterKeys, CustomFilter, DateFilterCondition, dateFilterKeys, Filter, NumberFilterCondition, numberFilterKeys, StringFilterCondition, stringFilterKeys } from '../models/customfilter';
import { mapMedia, Media } from '../models/media';
import { CustomfilterService } from '../services/customfilter.service';
import { MediaService } from '../services/media.service';
import { WebsocketService } from '../services/websocket.service';
import { AddCustomFilterDialogComponent } from "./add-filter-dialog/add-filter-dialog.component";
import { DisplayTitlePipe } from "./pipes/display-title.pipe";

@Component({
  selector: 'app-media2',
  imports: [
    FormsModule,
    NgTemplateOutlet,
    RouterLink,
    ScrollNearEndDirective,
    AddCustomFilterDialogComponent,
    DisplayTitlePipe
  ],
  templateUrl: './media.component.html',
  styleUrl: './media.component.css'
})
export class MediaComponent {

  constructor(
    private route: ActivatedRoute,
    private mediaService: MediaService,
    private webSocketService: WebsocketService
  ) { }

  customfilterService = inject(CustomfilterService);

  moviesOnly = signal<boolean | null>(null);
  isLoading = signal<boolean>(true);

  inEditMode: boolean = false;
  selectedMedia: number[] = [];

  sortOptions: (keyof Media)[] = ['title', 'year', 'added_at', 'updated_at'];
  filterOptions: string[] = ['all', 'downloaded', 'downloading', 'missing', 'monitored', 'unmonitored'];
  customFilters = signal<CustomFilter[]>([]);
  allFilters = computed(() => {
    return this.filterOptions.concat(this.customFilters().map(f => f.filter_name));
  });
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

  applyFilter(filter: Filter, media: Media): boolean {
    let filterValue = filter.filter_value;
    let filterBy = filter.filter_by;
    // Boolean filters
    if (booleanFilterKeys.includes(filterBy)) {
      let origValue = media[filterBy] as boolean;
      let filterValueBool = filterValue.toLowerCase() === 'true';
      return origValue === filterValueBool;
    }
    // Date filters
    if (dateFilterKeys.includes(filterBy)) {
      let mediaDate = new Date(media[filterBy] as string);
      let filterDate = new Date(filterValue);
      switch (filter.filter_condition) {
        case DateFilterCondition.IS_AFTER:
          return mediaDate > filterDate;
        case DateFilterCondition.IS_BEFORE:
          return mediaDate < filterDate;
        case DateFilterCondition.IN_THE_LAST:
          let last = new Date();
          last.setDate(last.getDate() - parseInt(filterValue));
          return mediaDate > last;
        case DateFilterCondition.NOT_IN_THE_LAST:
          let last2 = new Date();
          last2.setDate(last2.getDate() - parseInt(filterValue));
          return mediaDate < last2;
        case DateFilterCondition.EQUALS:
          return mediaDate.getDate() === filterDate.getDate();
        case DateFilterCondition.NOT_EQUALS:
          return mediaDate.getDate() !== filterDate.getDate();
        default:
          return true;
      }
    }
    // Number filters
    if (numberFilterKeys.includes(filterBy)) {
      let origValue = media[filterBy] as number;
      let filterValueNum = parseInt(filterValue);
      switch (filter.filter_condition) {
        case NumberFilterCondition.GREATER_THAN:
          return origValue > filterValueNum;
        case NumberFilterCondition.GREATER_THAN_EQUAL:
          return origValue >= filterValueNum;
        case NumberFilterCondition.LESS_THAN:
          return origValue < filterValueNum;
        case NumberFilterCondition.LESS_THAN_EQUAL:
          return origValue <= filterValueNum;
        case NumberFilterCondition.EQUALS:
          return origValue === filterValueNum;
        case NumberFilterCondition.NOT_EQUALS:
          return origValue !== filterValueNum;
        default:
          return true
      }
    }
    // String filters
    if (stringFilterKeys.includes(filterBy)) {
      let origValue = media[filterBy] as string;
      switch (filter.filter_condition) {
        case StringFilterCondition.CONTAINS:
          return origValue.includes(filterValue);
        case StringFilterCondition.NOT_CONTAINS:
          return !origValue.includes(filterValue);
        case StringFilterCondition.EQUALS:
          return origValue === filterValue;
        case StringFilterCondition.NOT_EQUALS:
          return origValue !== filterValue;
        case StringFilterCondition.STARTS_WITH:
          return origValue.startsWith(filterValue);
        case StringFilterCondition.NOT_STARTS_WITH:
          return !origValue.startsWith(filterValue);
        case StringFilterCondition.ENDS_WITH:
          return origValue.endsWith(filterValue);
        case StringFilterCondition.NOT_ENDS_WITH:
          return !origValue.endsWith(filterValue);
        case StringFilterCondition.IS_EMPTY:
          return origValue === '';
        case StringFilterCondition.IS_NOT_EMPTY:
          return origValue !== '';
        default:
          return true;
      }
    }
    return true;
  }

  filterDisplayed = false;
  applyCustomFilter(filter_name: string, media: Media): boolean {
    let customFilter = this.customFilters().find(f => f.filter_name === filter_name);
    if (!this.filterDisplayed) {
      console.log("Custom filter:", customFilter);
      this.filterDisplayed = true;
    }
    if (!customFilter) {
      return true;
    }
    // Apply filters until one of them returns false or all are applied 
    return customFilter.filters.every(filter => this.applyFilter(filter, media));
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
          // console.log("Applying custom filter:", this.selectedFilter());
          return this.applyCustomFilter(this.selectedFilter(), media);
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
    const delta = Math.min(Math.floor(Math.abs(currentTime - this.lastUpdateTime) / 1000), 1000);
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
    // Retrieve custom filters for the view from the server
    this.customfilterService.getViewFilters(moviesOnlyValue).subscribe(
      (filters) => {
        this.customFilters.set(filters);
      }
    );
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
  openFilterDialog(): void {
    this.addFilterDialog.nativeElement.showModal();
    if (this.customFilters().length === 0) {
      this.openFilterEditDialog(null);
    }
    // this.isCustomFilterDialogOpen = true;
  }
  editFilter: CustomFilter | null = null;
  openFilterEditDialog(filter: CustomFilter | null): void {
    // console.log("Edit filter:", filter);
    this.editFilter = filter;
    this.isCustomFilterDialogOpen = true;
  }

  deleteFilter(filter_id: number): void {
    this.customfilterService.delete(filter_id).subscribe(() => {
      this.customFilters.update((filters) => {
        return filters.filter(f => f.id !== filter_id);
      });
    });
  }

  closeFilterDialog(): void {
    this.addFilterDialog.nativeElement.close();
    this.retrieveSortNFilterOptions(); // Retrieve custom filters
    // Delay closing the dialog to prevent content disappearing immediately
    setTimeout(() => {
      this.isCustomFilterDialogOpen = false;
    }, 1000);
  }


}

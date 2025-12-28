import {ChangeDetectionStrategy, Component, computed, effect, ElementRef, inject, signal, viewChild, ViewContainerRef} from '@angular/core';
import {CustomFilter} from 'src/app/models/customfilter';
import {Media} from 'src/app/models/media';
import {CustomfilterService} from 'src/app/services/customfilter.service';
import {MediaService} from 'src/app/services/media.service';
import {AddCustomFilterDialogComponent} from '../../add-filter-dialog/add-filter-dialog.component';
import {DisplayTitlePipe} from '../../pipes/display-title.pipe';

@Component({
  selector: 'app-normal-header',
  imports: [DisplayTitlePipe],
  templateUrl: './normal-header.component.html',
  styleUrl: './normal-header.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NormalHeaderComponent {
  protected readonly customfilterService = inject(CustomfilterService);
  protected readonly mediaService = inject(MediaService);
  private viewContainerRef = inject(ViewContainerRef);

  // Constants from Media Service
  protected readonly defaultDisplayCount = this.mediaService.defaultDisplayCount;

  // Constants/Variables in this Component
  sortOptions: (keyof Media)[] = ['title', 'year', 'added_at', 'updated_at', 'downloaded_at'];
  filterOptions = signal<string[]>(['all', 'downloaded', 'downloading', 'missing', 'monitored', 'unmonitored']);

  // Signals from Media Service
  protected readonly checkedMediaIDs = this.mediaService.checkedMediaIDs;
  protected readonly displayCount = this.mediaService.displayCount;
  protected readonly inEditMode = this.mediaService.inEditMode;
  protected readonly moviesOnly = this.mediaService.moviesOnly;
  protected readonly selectedSort = this.mediaService.selectedSort;
  protected readonly sortAscending = this.mediaService.sortAscending;
  protected readonly selectedFilter = this.mediaService.selectedFilter;

  // Signals from Custom Filter Service
  protected readonly customFilters = this.customfilterService.viewFilters;

  // Signals in this Component
  allFilters = computed(() => {
    return this.filterOptions().concat(this.customFilters().map((f) => f.filter_name));
  });

  // Effect to retrieve sort and filter options when moviesOnly changes
  effect1 = effect(() => {
    // Your effect logic here
    const moviesOnlyValue = this.moviesOnly();
    // If moviesOnly is set to null (Home Page), change filter options and reset defaults
    if (moviesOnlyValue === null) {
      this.filterOptions.set(['all', 'movies', 'series']);
      this.selectedFilter.set('all');
      this.selectedSort.set('updated_at');
      this.sortAscending.set(false);
    }
    // Retrieve the sort option from the local session
    this.retrieveSortNFilterOptions(moviesOnlyValue);
  });

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
  retrieveSortNFilterOptions(moviesOnlyValue: boolean | null): void {
    const pageType = moviesOnlyValue == null ? 'AllMedia' : moviesOnlyValue ? 'Movies' : 'Series';
    // Retrieve the filter option from the local session
    let filterOption = localStorage.getItem(`Trailarr${pageType}Filter`);
    if (filterOption) {
      this.selectedFilter.set(filterOption);
    }
    // Retrieve the sort option from the local session
    let savedSortOption = localStorage.getItem(`Trailarr${pageType}Sort`);
    let savedSortAscending = localStorage.getItem(`Trailarr${pageType}SortAscending`);
    if (savedSortOption) {
      this.selectedSort.set(savedSortOption as keyof Media);
    }
    if (savedSortAscending) {
      this.sortAscending.set(savedSortAscending == 'true');
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
    this.checkedMediaIDs.set([]); // Clear the selected media items
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
    const moviesOnlyValue = this.moviesOnly();
    const pageType = moviesOnlyValue == null ? 'AllMedia' : moviesOnlyValue ? 'Movies' : 'Series';
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
    this.checkedMediaIDs.set([]); // Clear the selected media items
    // Reset the display count to the default
    this.displayCount.set(this.defaultDisplayCount);
    // Set the filter option
    this.selectedFilter.set(filterBy);
    // Save the filter option to the local session
    const moviesOnlyValue = this.moviesOnly();
    const pageType = moviesOnlyValue == null ? 'AllMedia' : moviesOnlyValue ? 'Movies' : 'Series';
    localStorage.setItem(`Trailarr${pageType}Filter`, this.selectedFilter());
    return;
  }

  readonly showFiltersDialog = viewChild.required<ElementRef<HTMLDialogElement>>('showFiltersDialog');

  openFilterDialog(): void {
    if (this.customFilters().length === 0) {
      this.openFilterEditDialog(null);
    } else {
      this.showFiltersDialog().nativeElement.showModal();
    }
    // this.isCustomFilterDialogOpen = true;
  }

  openFilterEditDialog(filter: CustomFilter | null): void {
    this.showFiltersDialog().nativeElement.close();
    // Open the dialog for adding or editing a custom filter
    const dialogRef = this.viewContainerRef.createComponent(AddCustomFilterDialogComponent);
    dialogRef.setInput('customFilter', filter);
    dialogRef.setInput('filterType', this.moviesOnly() == null ? 'HOME' : this.moviesOnly() ? 'MOVIES' : 'SERIES');
    dialogRef.instance.dialogClosed.subscribe(() => {
      // Filter dialog closed, reload filters
      this.customfilterService.reloadFilters();
      this.retrieveSortNFilterOptions(this.moviesOnly());
      setTimeout(() => {
        dialogRef.destroy(); // Destroy the dialog component after use
      }, 3000);
    });
  }

  deleteFilter(filter_id: number): void {
    this.customfilterService.delete(filter_id).subscribe(() => {
      this.customfilterService.reloadFilters();
    });
  }

  closeFilterDialog(): void {
    this.showFiltersDialog().nativeElement.close();
    this.retrieveSortNFilterOptions(this.moviesOnly()); // Retrieve custom filters
  }
}

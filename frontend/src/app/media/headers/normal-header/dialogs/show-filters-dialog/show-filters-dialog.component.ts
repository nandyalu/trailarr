import {AfterViewInit, ChangeDetectionStrategy, Component, computed, ElementRef, inject, output, signal, viewChild} from '@angular/core';
import {EditFilterDialogComponent} from 'src/app/media/dialogs/edit-filter-dialog/edit-filter-dialog.component';
import {CustomFilter} from 'src/app/models/customfilter';
import {CustomfilterService} from 'src/app/services/customfilter.service';
import {MediaService} from 'src/app/services/media.service';

@Component({
  selector: 'show-filters-dialog',
  imports: [EditFilterDialogComponent],
  templateUrl: './show-filters-dialog.component.html',
  styleUrl: './show-filters-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ShowFiltersDialogComponent implements AfterViewInit {
  private readonly customfilterService = inject(CustomfilterService);
  private readonly mediaService = inject(MediaService);

  // Signals from Custom Filter Service
  protected readonly viewCustomFilters = this.customfilterService.viewFilters;

  // Signals from Media Service
  private readonly moviesOnly = this.mediaService.moviesOnly;

  // Signals in this Component
  /** `protected` `readonly` Signal to toggle the Add/Edit Filter Dialog */
  protected readonly editFilterDialogOpen = signal(false);
  /** `protected` `readonly` Signal to hold the filter being edited */
  protected readonly filterToEdit = signal<CustomFilter | null>(null);
  /** `protected` `readonly` Computed signal to determine the filter type */
  protected readonly filterType = computed(() => {
    return this.moviesOnly() == null ? 'HOME' : this.moviesOnly() ? 'MOVIES' : 'SERIES';
  });

  /** `readonly` Event emitter to notify when the dialog is closed */
  readonly closed = output<void>();

  private readonly dialog = viewChild.required<ElementRef<HTMLDialogElement>>('showFiltersDialog');

  ngAfterViewInit(): void {
    this.openDialog();
  }

  /**
   * Opens the appropriate dialog based on the current state of custom filters.
   * If no custom filters exist, opens the edit filter dialog directly.
   * Otherwise, displays the show filters dialog.
   * @private Only used from `ngAfterViewInit` to open the dialog on component load
   */
  private openDialog(): void {
    if (this.viewCustomFilters().length === 0) {
      // If there are no custom filters, directly open the Add Filter Dialog
      this.openFilterEditDialog(null);
    } else {
      // Open the Show Filters Dialog
      this.editFilterDialogOpen.set(false);
      this.dialog().nativeElement.showModal();
    }
  }

  /**
   * Deletes a custom filter by its ID and reloads the filters list.
   * @param filter_id - The unique identifier of the filter to delete
   */
  protected deleteFilter(filter_id: number): void {
    this.customfilterService.delete(filter_id).subscribe(() => {
      this.customfilterService.reloadFilters();
    });
  }

  /**
   * Closes the dialog and emits a closed event.
   *
   * This method closes the native dialog element and emits a `closed` event after a brief delay
   * to allow the dialog closing animation to complete smoothly.
   *
   * @protected Only used within the component template
   * @returns {void}
   */
  protected closeDialog(emit: boolean): void {
    this.dialog().nativeElement.close();
    if (!emit) {
      return;
    }
    // Emit the closed event after a short delay to allow the dialog to close smoothly
    setTimeout(() => {
      this.closed.emit();
    }, 500);
  }

  /**
   * Opens the filter edit dialog for a selected custom filter (if any).
   * Closes the current filter display dialog, sets the filter to be edited,
   * and marks the edit dialog as open.
   *
   * @protected Only used within the component template
   * @param filter - The custom filter to edit, or null to create a new filter
   */
  protected openFilterEditDialog(filter: CustomFilter | null): void {
    this.closeDialog(false);
    this.filterToEdit.set(filter);
    this.editFilterDialogOpen.set(true);
  }

  /**
   * Handles the closure of the edit filter dialog.
   * Closes the dialog, reloads the custom filters, and emits a closed event after a delay.
   * @protected
   * @returns {void}
   */
  protected onEditDialogClosed(): void {
    this.editFilterDialogOpen.set(false);
    this.customfilterService.reloadFilters();
    setTimeout(() => {
      this.closed.emit();
    }, 500);
  }
}

import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  effect,
  ElementRef,
  inject,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import {customError, Field, FieldTree, form, submit} from '@angular/forms/signals';
import {firstValueFrom} from 'rxjs';
import {DisplayTitlePipe} from 'src/app/helpers/display-title.pipe';
import {allFilterKeys, CustomFilter, CustomFilterCreate, FilterCreate, FilterType} from 'src/app/models/customfilter';
import {CustomfilterService} from 'src/app/services/customfilter.service';
import {HelpLinkIconComponent} from 'src/app/shared/help-link-icon/help-link-icon.component';
import {customFilterSchema, getFilterConditions, getFilterValueType, newCustomFilter, newFilter} from './form-schema';

@Component({
  selector: 'edit-filter-dialog',
  imports: [DisplayTitlePipe, HelpLinkIconComponent, Field],
  templateUrl: './edit-filter-dialog.component.html',
  styleUrl: './edit-filter-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditFilterDialogComponent implements AfterViewInit {
  protected readonly helpLink = 'https://nandyalu.github.io/trailarr/user-guide/settings/profiles/filters/';

  // Component inputs
  readonly filterType = input.required<keyof typeof FilterType>();
  // If an existing custom filter is provided, the form will be initialized for updating;
  // otherwise it is assumed you are creating a new one.
  readonly customFilter = input<CustomFilter | null>(null);

  // Component outputs
  /** Emits the ID of the custom filter when the dialog is closed
   *
   * If the dialog is closed without saving, emits `-1` else emits the ID of the created/updated filter.
   */
  readonly dialogClosed = output<number>();

  // Component signals
  protected readonly customfilterService = inject(CustomfilterService);
  /** Signal to hold the form data for the custom filter */
  protected readonly customFilterData = signal<CustomFilterCreate>({...newCustomFilter});

  // Component effects
  /** Effect to update customFilterData when customFilter input changes */
  protected customFilterDataEffect = effect(() => {
    const customFilterValue = this.customFilter();
    if (customFilterValue) {
      this.customFilterData.set({...customFilterValue});
    }
  });

  private readonly dialog = viewChild.required<ElementRef<HTMLDialogElement>>('editCustomFilterDialog');

  ngAfterViewInit(): void {
    this.openDialog();
  }

  private openDialog(): void {
    this.dialog().nativeElement.showModal();
  }

  protected closeDialog(id: number): void {
    this.dialog().nativeElement.close();
    setTimeout(() => {
      this.dialogClosed.emit(id);
    }, 500);
  }

  // Form constants
  // Get all filter keys.
  protected readonly filterKeys = allFilterKeys;

  // Get the filter conditions for a given filter key.
  protected getFilterConditions = getFilterConditions;

  // Get the filter value type for a given filter key.
  protected getFilterValueType = getFilterValueType;

  // Adds a new filter to the filters array.
  protected addFilter(): void {
    this.customFilterData.update((data) => {
      return {
        ...data,
        filters: [...data.filters, {...newFilter, customfilter_id: data.id}],
      };
    });
  }

  // Removes a filter from the filters array.
  protected removeFilter(index: number): void {
    this.customFilterData.update((data) => {
      const newFilters = [...data.filters];
      newFilters.splice(index, 1);
      return {
        ...data,
        filters: newFilters,
      };
    });
    this.customFilterForm.filters().markAsDirty();
  }

  // Value change listener for the filter_by control.
  protected onFilterByChange(filter: FieldTree<FilterCreate, number>): void {
    filter.filter_condition().reset(undefined);
    // filter.filter_condition().setControlValue('' as any);
    filter.filter_value().reset('');
    // filter.filter_value().setControlValue('');
  }

  // Value change listener for the filter_condition control.
  protected onFilterConditionChange(filter: FieldTree<FilterCreate, number>): void {
    filter.filter_value().reset('');
    // filter.filter_value().setControlValue('');
  }

  // Signal Form
  /** Signal Form for CustomFilter */
  protected readonly customFilterForm = form(this.customFilterData, customFilterSchema);
  protected readonly submitResult = signal<{type: 'success' | 'error'; message: string}>({type: 'success', message: ''});

  // Called when the form is submitted. This will trigger validation and then submit to server if valid.
  protected async formSubmit(event: Event): Promise<void> {
    event.preventDefault();
    this.submitResult.set({type: 'success', message: ''});
    await submit(this.customFilterForm, async () => {
      let formData = this.customFilterData();
      formData.filter_type = FilterType[this.filterType()];
      try {
        let result: CustomFilter;
        if (formData.id) {
          // If id exists, update it
          result = await firstValueFrom(this.customfilterService.update(formData as CustomFilter));
        } else {
          // Otherwise, create a new CustomFilter.
          result = await firstValueFrom(this.customfilterService.create(formData));
        }
        this.submitResult.set({type: 'success', message: 'Filters saved successfully!'});
        setTimeout(() => {
          this.closeDialog(result.id);
        }, 3000);
        return undefined; // Return undefined to indicate success
      } catch (error) {
        console.error('Error submitting form:', error);
        this.submitResult.set({type: 'error', message: 'Error submitting form.' + (error as Error).message});
        return customError({
          message: 'An error occurred while submitting the form. Please try again.',
        });
      }
    });
  }
}

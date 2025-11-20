import {Component, computed, effect, ElementRef, EventEmitter, inject, input, Output, viewChild} from '@angular/core';
import {FormArray, FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators} from '@angular/forms';

import {HelpLinkIconComponent} from 'src/app/shared/help-link-icon/help-link-icon.component';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {
  BooleanFilterCondition,
  booleanFilterKeys,
  CustomFilterCreate,
  DateFilterCondition,
  dateFilterKeys,
  FilterCreate,
  FilterType,
  NumberFilterCondition,
  numberFilterKeys,
  StringFilterCondition,
  stringFilterKeys,
} from '../../models/customfilter'; // adjust the path as necessary
import {Media} from '../../models/media';
import {CustomfilterService} from '../../services/customfilter.service';

@Component({
  selector: 'app-add-filter-dialog',
  imports: [FormsModule, HelpLinkIconComponent, LoadIndicatorComponent, ReactiveFormsModule],
  templateUrl: './add-filter-dialog.component.html',
  styleUrl: './add-filter-dialog.component.scss',
})
export class AddCustomFilterDialogComponent {
  private readonly fb = inject(FormBuilder);
  helpLink = 'https://nandyalu.github.io/trailarr/user-guide/settings/profiles/filters/';

  filterType = input.required<string>();
  filterTypeValue = computed(() => {
    let _filterType = this.filterType().toUpperCase();
    if (_filterType == 'MOVIES') {
      return FilterType.MOVIES;
    }
    if (_filterType == 'SERIES') {
      return FilterType.SERIES;
    }
    if (_filterType == 'TRAILER') {
      return FilterType.TRAILER;
    }
    return FilterType.HOME;
  });
  // If an existing custom filter is provided, the form will be initialized for updating;
  // otherwise it is assumed you are creating a new one.
  customFilter = input<CustomFilterCreate | null>(null);

  @Output() dialogClosed = new EventEmitter<number>();

  isLoading = true;

  customfilterService = inject(CustomfilterService);

  customFilterForm!: FormGroup;

  computedSignal = computed(() => {
    let customFilterData = this.customFilter();
    this.initForm(customFilterData);
    return true;
  });

  // Get all enum values for select options.
  boolFilterConditions = Object.values(BooleanFilterCondition);
  dateFilterConditions = Object.values(DateFilterCondition);
  numberFilterConditions = Object.values(NumberFilterCondition);
  stringFilterConditions = Object.values(StringFilterCondition);
  filterConditions: string[][] = [] as string[][];
  filterValueTypes: string[] = [];
  // Get all filter keys and sort them.
  filterKeys = booleanFilterKeys.concat(dateFilterKeys, numberFilterKeys, stringFilterKeys).sort();

  viewForOptions = Object.values(FilterType);
  readonly customFilterDialog = viewChild.required<ElementRef<HTMLDialogElement>>('customFilterDialog');

  constructor() {
    effect(() => {
      this.initForm(this.customFilter());
    });
  }

  ngAfterViewInit() {
    this.customFilterDialog().nativeElement.showModal();
  }

  closeDialog(emitValue: number): void {
    this.customFilterDialog().nativeElement.close();
    this.dialogClosed.emit(emitValue);
    // setTimeout(() => {
    // }, 2000);
    this.filters.clear();
    this.addFilter();
    this.customFilterForm.reset();
  }

  displayTitle(value: string): string {
    return value
      .toLowerCase()
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  initForm(customFilterData: CustomFilterCreate | null): FormGroup {
    // Initialize the form.
    let _form = this.fb.group({
      id: [customFilterData ? customFilterData.id : null],
      filter_type: [customFilterData ? customFilterData.filter_type : this.filterTypeValue(), Validators.required],
      filter_name: [customFilterData ? customFilterData.filter_name : '', [Validators.required, Validators.maxLength(100)]],
      filters: this.fb.array([], Validators.required), // Will hold an array of filters.
    });
    this.customFilterForm = _form;

    // If updating an existing CustomFilter, populate the filters FormArray.
    if (customFilterData && customFilterData.filters && customFilterData.filters.length) {
      customFilterData.filters.forEach((filter) => {
        this.addFilter(filter);
      });
    } else {
      // Otherwise, initialize with one empty filter.
      this.addFilter();
    }
    this.isLoading = false;
    return _form;
  }

  // Getter for the filters FormArray.
  get filters(): FormArray {
    return this.customFilterForm.get('filters') as FormArray;
  }

  // Creates a FormGroup for a single filter.
  createFilter(filter?: FilterCreate): FormGroup {
    return this.fb.group({
      id: [filter ? filter.id : null],
      filter_by: [filter ? filter.filter_by : '', Validators.required],
      filter_condition: [filter ? filter.filter_condition : '', Validators.required],
      filter_value: [filter ? filter.filter_value : '', Validators.required],
      customfilter_id: [filter ? filter.customfilter_id : null],
    });
  }

  // Get the filter conditions for a given filter key.
  getFilterConditions(filterKey: keyof Media): string[] {
    if (booleanFilterKeys.includes(filterKey)) {
      return this.boolFilterConditions;
    } else if (dateFilterKeys.includes(filterKey)) {
      return this.dateFilterConditions;
    } else if (numberFilterKeys.includes(filterKey)) {
      return this.numberFilterConditions;
    } else if (stringFilterKeys.includes(filterKey)) {
      return this.stringFilterConditions;
    }
    return [];
  }

  // Get the filter value type for a given filter key.
  getFilterValueType(filterKey: keyof Media, filterCondition: string): string {
    if (booleanFilterKeys.includes(filterKey)) {
      return 'boolean';
    } else if (dateFilterKeys.includes(filterKey)) {
      if (filterCondition === DateFilterCondition.IN_THE_LAST || filterCondition === DateFilterCondition.NOT_IN_THE_LAST) {
        return 'number_days';
      }
      return 'date';
    } else if (numberFilterKeys.includes(filterKey)) {
      return 'number';
    }
    return 'string';
  }

  // Adds a new filter FormGroup to the filters FormArray.
  addFilter(filter?: FilterCreate): void {
    if (filter && filter.filter_by) {
      // If a filter is provided, set the filter_condition control to required.
      this.filterConditions.push(this.getFilterConditions(filter.filter_by));
      this.filterValueTypes.push(this.getFilterValueType(filter.filter_by, filter.filter_condition));
    } else {
      this.filterConditions.push([]);
      this.filterValueTypes.push('string');
    }
    this.filters.push(this.createFilter(filter));
  }

  // Removes a filter FormGroup from the filters FormArray.
  removeFilter(index: number): void {
    this.filterConditions.splice(index, 1);
    this.filters.removeAt(index);
  }

  // Add a value change listener for the filter_by control.
  onFilterByChange(event: Event, index: number): void {
    // Get the filter_by control.
    const filterByControl = this.filters.at(index).get('filter_by')?.value as keyof Media;
    // Update the filter_conditions array for this filter.
    this.filterConditions[index] = this.getFilterConditions(filterByControl);
    // Update the filter_value_type for this filter.
    this.filterValueTypes[index] = this.getFilterValueType(filterByControl, '');
    // Reset the filter_condition and filter_value controls.
    this.filters.at(index).get('filter_condition')?.setValue('');
    if (booleanFilterKeys.includes(filterByControl)) {
      this.filters.at(index).get('filter_condition')?.setValue(BooleanFilterCondition.EQUALS);
    }
    this.filters.at(index).get('filter_value')?.reset();
  }

  onFilterConditionChange(event: Event, index: number): void {
    // Get the filter_by control.
    const filterByControl = this.filters.at(index).get('filter_by')?.value as keyof Media;
    // Set the filter_value_type based on selected condition
    // Sets to number if the condition is IN_THE_LAST or NOT_IN_THE_LAST.
    if (event.target) {
      const filterCondition = (event.target as HTMLSelectElement).value;
      this.filterValueTypes[index] = this.getFilterValueType(filterByControl, filterCondition);
    }
    // Reset the filter_value control.
    this.filters.at(index).get('filter_value')?.reset();
  }

  // Called when the form is submitted.
  submitting: boolean = false;
  onSubmit(): void {
    if (this.submitting) {
      return;
    }
    this.submitting = true;
    if (this.customFilterForm.valid) {
      // Convert all filter values to strings.
      let formData = this.customFilterForm.value;
      formData.filters.forEach((filter: FilterCreate) => {
        filter.filter_value = filter.filter_value.toString();
      });
      if (this.customFilter()?.id) {
        // If id exists, update it
        this.customfilterService.update(formData).subscribe((value) => {
          this.closeDialog(value.id);
          this.submitting = false;
        });
      } else {
        // Otherwise, create a new CustomFilter.
        this.customfilterService.create(formData).subscribe((value) => {
          this.closeDialog(value.id);
          this.submitting = false;
        });
      }
    } else {
      // Debugging: Log all invalid form controls.
      // for (const key of Object.keys(this.customFilterForm.controls)) {
      //   const control = this.customFilterForm.get(key);
      //   if (control?.invalid) {
      //     console.log(`F: ${key} is invalid: ${control}`);
      //   }
      //   if (control instanceof FormGroup || control instanceof FormArray) {
      //     for (const innerKey of Object.keys(control.controls)) {
      //       const innerControl = control.get(innerKey);
      //       if (innerControl?.invalid) {
      //         console.log(`Inner: ${key}.${innerKey} is invalid: ${innerControl}`);
      //       }
      //     }
      //   } else {
      //     if (control?.invalid) {
      //       console.log(`${key} is invalid: ${control}`);
      //     }
      //   }
      // }
      console.log('Form is invalid');
      // Optionally mark all fields as touched to show validation errors.
      this.customFilterForm.markAllAsTouched();
      this.submitting = false;
    }
  }
}

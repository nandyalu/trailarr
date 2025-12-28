import {applyEach, maxLength, readonly, required, schema} from '@angular/forms/signals';
import {BooleanFilterCondition, booleanFilterKeys, CustomFilterCreate, DateFilterCondition, dateFilterKeys, FilterCreate, FilterType, NumberFilterCondition, numberFilterKeys, StringFilterCondition, stringFilterKeys} from 'src/app/models/customfilter';
import { Media } from 'src/app/models/media';

export const filterSchema = schema<FilterCreate>((schema) => {
  readonly(schema.id);
  readonly(schema.customfilter_id);
  required(schema.filter_by, {message: 'Filter By is required.'});
  required(schema.filter_condition, {
    message: 'Filter Condition is required.',
    when: ({valueOf}) => (valueOf(schema.filter_by) as any) !== '',
  });
  required(schema.filter_value, {
    message: 'Filter Value is required.',
    when: ({valueOf}) => {
      const filterCondition = valueOf(schema.filter_condition);
      if (filterCondition === StringFilterCondition.IS_EMPTY || filterCondition === StringFilterCondition.IS_NOT_EMPTY) {
        return false;
      }
      return (valueOf(schema.filter_condition) as any) !== ''
    },
  });
});

export const newFilter: FilterCreate = {
  id: null,
  customfilter_id: null,
  filter_by: '' as any,
  filter_condition: '' as any,
  filter_value: '',
};

export const customFilterSchema = schema<CustomFilterCreate>((schema) => {
  readonly(schema.id);
  readonly(schema.filter_type);
  required(schema.filter_name, {message: 'Filter Name is required.'});
  maxLength(schema.filter_name, 100, {message: 'Filter Name cannot exceed 100 characters.'});
  applyEach(schema.filters, filterSchema);
  required(schema.filters, {message: 'At least one filter is required.'});
});

export const newCustomFilter: CustomFilterCreate = {
  id: null,
  filter_name: '',
  filter_type: FilterType.HOME,
  filters: [{...newFilter}],
};

// Get all enum values for select options.
const boolFilterConditions = Object.values(BooleanFilterCondition);
const dateFilterConditions = Object.values(DateFilterCondition);
const numberFilterConditions = Object.values(NumberFilterCondition);
const stringFilterConditions = Object.values(StringFilterCondition);

// Get the filter conditions for a given filter key.
export function getFilterConditions(filterKey: '' | keyof Media): string[] {
  if (filterKey === '') {
    return [];
  }
  if (booleanFilterKeys.includes(filterKey)) {
    return boolFilterConditions;
  } else if (dateFilterKeys.includes(filterKey)) {
    return dateFilterConditions;
  } else if (numberFilterKeys.includes(filterKey)) {
    return numberFilterConditions;
  } else if (stringFilterKeys.includes(filterKey)) {
    return stringFilterConditions;
  }
  return [];
}

// Get the filter value type for a given filter key.
export function getFilterValueType(filterKey: keyof Media, filterCondition: string): string {
  if (booleanFilterKeys.includes(filterKey)) {
    return 'boolean';
  } else if (dateFilterKeys.includes(filterKey)) {
    if (filterCondition === DateFilterCondition.IN_THE_LAST || filterCondition === DateFilterCondition.NOT_IN_THE_LAST) {
      return 'number_days';
    }
    return 'date';
  } else if (numberFilterKeys.includes(filterKey)) {
    return 'number';
  } else if (stringFilterKeys.includes(filterKey)) {
    if (filterCondition === StringFilterCondition.IS_EMPTY || filterCondition === StringFilterCondition.IS_NOT_EMPTY) {
      return 'none';
    }
    return 'string';
  }
  return 'string';
}

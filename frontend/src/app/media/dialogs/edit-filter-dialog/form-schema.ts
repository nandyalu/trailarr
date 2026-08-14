import {applyEach, maxLength, readonly, required, schema} from '@angular/forms/signals';
import {
  allFilterKeys,
  BooleanFilterCondition,
  booleanFilterKeys,
  CustomFilterCreate,
  DateFilterCondition,
  dateFilterKeys,
  FileFilterCondition,
  fileFilterKeys,
  FilterCreate,
  FilterType,
  NumberFilterCondition,
  numberFilterKeys,
  StringFilterCondition,
  stringFilterKeys,
  viewOnlyFilterKeys,
} from 'src/app/models/customfilter';

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
      return (valueOf(schema.filter_condition) as any) !== '';
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

/** One group of fields in the filter editor's field picker. */
export interface FilterFieldGroup {
  label: string;
  keys: string[];
}

/**
 * Returns the grouped field lists for the filter editor's field picker.
 *
 * Profile (TRAILER) filters do not get the Downloads group: the backend
 * rejects download fields on profiles — a profile that filters on its own
 * downloads is circular. Media and Files fields are available to all types.
 */
export function getFilterFieldGroups(filterType: keyof typeof FilterType): FilterFieldGroup[] {
  const mediaKeys = allFilterKeys.filter((k) => !viewOnlyFilterKeys.includes(k) && !fileFilterKeys.includes(k));
  const groups: FilterFieldGroup[] = [{label: 'Media', keys: mediaKeys}];
  if (filterType !== 'TRAILER') {
    groups.push({label: 'Downloads', keys: [...viewOnlyFilterKeys].sort()});
  }
  groups.push({label: 'Files', keys: fileFilterKeys});
  return groups;
}

// Get all enum values for select options.
const boolFilterConditions = Object.values(BooleanFilterCondition);
const dateFilterConditions = Object.values(DateFilterCondition);
const numberFilterConditions = Object.values(NumberFilterCondition);
const stringFilterConditions = Object.values(StringFilterCondition);

// Get the filter conditions for a given filter key.
export function getFilterConditions(filterKey: string): string[] {
  if (filterKey === '') {
    return [];
  }
  if (filterKey === 'download_profile') {
    // A profile either owns a download or it does not — ordering
    // conditions make no sense for an id.
    return [NumberFilterCondition.EQUALS, NumberFilterCondition.NOT_EQUALS];
  }
  if (booleanFilterKeys.includes(filterKey)) {
    return boolFilterConditions;
  } else if (dateFilterKeys.includes(filterKey)) {
    return dateFilterConditions;
  } else if (numberFilterKeys.includes(filterKey)) {
    return numberFilterConditions;
  } else if (stringFilterKeys.includes(filterKey)) {
    return stringFilterConditions;
  } else if (fileFilterKeys.includes(filterKey)) {
    return Object.values(FileFilterCondition);
  }
  return [];
}

// Get the filter value type for a given filter key.
export function getFilterValueType(filterKey: string, filterCondition: string): string {
  if (filterKey === 'download_profile') {
    // Rendered as a profile dropdown that stores the profile id
    return 'profile';
  }
  if (booleanFilterKeys.includes(filterKey)) {
    return 'boolean';
  } else if (dateFilterKeys.includes(filterKey)) {
    if (filterCondition === DateFilterCondition.IN_THE_LAST || filterCondition === DateFilterCondition.NOT_IN_THE_LAST) {
      return 'number_days';
    }
    return 'date';
  } else if (numberFilterKeys.includes(filterKey)) {
    return 'number';
  } else if (fileFilterKeys.includes(filterKey)) {
    return 'string';
  } else if (stringFilterKeys.includes(filterKey)) {
    if (filterCondition === StringFilterCondition.IS_EMPTY || filterCondition === StringFilterCondition.IS_NOT_EMPTY) {
      return 'none';
    }
    return 'string';
  }
  return 'string';
}

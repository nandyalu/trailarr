import { Media } from "./media";

export enum BooleanFilterCondition {
  // IS_TRUE = 'IS_TRUE',
  // IS_FALSE = 'IS_FALSE',
  EQUALS = 'EQUALS'
}

export enum DateFilterCondition {
  IS_AFTER = 'IS_AFTER',
  IS_BEFORE = 'IS_BEFORE',
  IN_THE_LAST = 'IN_THE_LAST',
  NOT_IN_THE_LAST = 'NOT_IN_THE_LAST',
  EQUALS = 'EQUALS',
  NOT_EQUALS = 'NOT_EQUALS',
}

export enum NumberFilterCondition {
  GREATER_THAN = 'GREATER_THAN',
  GREATER_THAN_EQUAL = 'GREATER_THAN_EQUAL',
  LESS_THAN = 'LESS_THAN',
  LESS_THAN_EQUAL = 'LESS_THAN_EQUAL',
  EQUALS = 'EQUALS',
  NOT_EQUALS = 'NOT_EQUALS',
}

export enum StringFilterCondition {
  CONTAINS = 'CONTAINS',
  NOT_CONTAINS = 'NOT_CONTAINS',
  EQUALS = 'EQUALS',
  NOT_EQUALS = 'NOT_EQUALS',
  STARTS_WITH = 'STARTS_WITH',
  NOT_STARTS_WITH = 'NOT_STARTS_WITH',
  ENDS_WITH = 'ENDS_WITH',
  NOT_ENDS_WITH = 'NOT_ENDS_WITH',
  IS_EMPTY = 'IS_EMPTY',
  IS_NOT_EMPTY = 'IS_NOT_EMPTY',
}

// export enum FilterCondition {
//   // Boolean conditions
//   IS_TRUE = 'IS_TRUE',
//   IS_FALSE = 'IS_FALSE',

//   // String conditions
//   CONTAINS = 'CONTAINS',
//   NOT_CONTAINS = 'NOT_CONTAINS',
//   EQUAL = 'EQUAL',
//   NOT_EQUAL = 'NOT_EQUAL',
//   STARTS_WITH = 'STARTS_WITH',
//   NOT_START_WITH = 'NOT_START_WITH',
//   ENDS_WITH = 'ENDS_WITH',
//   NOT_END_WITH = 'NOT_END_WITH',
//   IS_EMPTY = 'IS_EMPTY',
//   IS_NOT_EMPTY = 'IS_NOT_EMPTY',

//   // Number conditions
//   GREATER = 'GREATER_THAN',
//   GREATER_THAN_EQUAL = 'GREATER_THAN_EQUAL',
//   LESS_THAN = 'LESS_THAN',
//   LESS_THAN_EQUAL = 'LESS_THAN_EQUAL',
//   // Also include 'EQUAL' and 'NOT_EQUAL' from string conditions.

//   // Date conditions
//   IS_AFTER = 'IS_AFTER',
//   IS_BEFORE = 'IS_BEFORE',
//   IN_THE_LAST = 'IN_THE_LAST',
//   NOT_IN_THE_LAST = 'NOT_IN_THE_LAST',
// }

export type FilterCondition = BooleanFilterCondition | StringFilterCondition | NumberFilterCondition | DateFilterCondition;

export const booleanFilterKeys: (keyof Media)[] = [
  'arr_monitored',
  'is_movie',
  'monitor',
  'trailer_exists',
];

export const dateFilterKeys: (keyof Media)[] = [
  'added_at',
  'downloaded_at',
  'updated_at',
];

export const numberFilterKeys: (keyof Media)[] = [
  'arr_id',
  'connection_id',
  'id',
  'runtime',
  'year',
];

export const stringFilterKeys: (keyof Media)[] = [
  'folder_path',
  'imdb_id',
  'language',
  'overview',
  'status',
  'title',
  'txdb_id',
  'youtube_trailer_id',
];

export interface Filter {
  id: number;
  filter_by: keyof Media;
  filter_condition: FilterCondition;
  filter_value: string;
  customfilter_id: number;
}

export interface FilterCreate {
  id: number | null;
  filter_by: keyof Media;
  filter_condition: FilterCondition;
  filter_value: string;
  customfilter_id: number | null;
}

export enum FilterType {
  HOME = 'HOME',
  MOVIES = 'MOVIES',
  SERIES = 'SERIES',
  TRAILER = 'TRAILER',
}

export interface CustomFilter {
  id: number;
  filter_type: FilterType;
  filter_name: string;

  filters: Filter[];
}

export interface CustomFilterCreate {
  id: number | null;
  filter_type: FilterType;
  filter_name: string;

  filters: FilterCreate[];
}
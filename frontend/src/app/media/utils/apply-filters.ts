import {
  booleanFilterKeys,
  CustomFilter,
  DateFilterCondition,
  dateFilterKeys,
  fileFilterKeys,
  Filter,
  NumberFilterCondition,
  numberFilterKeys,
  StringFilterCondition,
  stringFilterKeys,
  virtualBooleanFilterKeys,
  virtualDateFilterKeys,
  virtualNumberFilterKeys,
} from 'src/app/models/customfilter';
import { FileFolderInfo } from 'src/app/models/filefolderinfo';
import {Media} from 'src/app/models/media';
import {CacheDecorator} from 'src/util';

// Virtual fields read from the media's download rows. 'file_count' is the one
// virtual field that reads files instead, so it is excluded here.
const downloadFilterKeys = [...virtualBooleanFilterKeys, ...virtualNumberFilterKeys, ...virtualDateFilterKeys].filter((k) => k !== 'file_count');

// ParserCache class with cached parsing methods
class ParserCache {
  @CacheDecorator()
  static parseDate(value: string): Date {
    return new Date(value);
  }

  @CacheDecorator()
  static parseNumber(value: string): number {
    return parseFloat(value);
  }

  @CacheDecorator()
  static getDaysAgo(days: number): Date {
    const d = new Date();
    d.setDate(d.getDate() - days);
    return d;
  }
}

// Cached filter functions
class FilterFunctions {
  @CacheDecorator()
  static applyBooleanFilter(value: boolean, filterValue: boolean): boolean {
    return value === filterValue;
  }

  @CacheDecorator()
  static applyNumberFilter(value: number, filterValue: number, condition: NumberFilterCondition): boolean {
    switch (condition) {
      case NumberFilterCondition.GREATER_THAN:
        return value > filterValue;
      case NumberFilterCondition.GREATER_THAN_EQUAL:
        return value >= filterValue;
      case NumberFilterCondition.LESS_THAN:
        return value < filterValue;
      case NumberFilterCondition.LESS_THAN_EQUAL:
        return value <= filterValue;
      case NumberFilterCondition.EQUALS:
        return value === filterValue;
      case NumberFilterCondition.NOT_EQUALS:
        return value !== filterValue;
      default:
        return true;
    }
  }

  @CacheDecorator()
  static applyDateFilter(mediaDate: Date, filterDate: Date, condition: DateFilterCondition, daysAgo?: Date): boolean {
    switch (condition) {
      case DateFilterCondition.IS_AFTER:
        return mediaDate > filterDate;
      case DateFilterCondition.IS_BEFORE:
        return mediaDate < filterDate;
      case DateFilterCondition.IN_THE_LAST:
        return daysAgo ? mediaDate > daysAgo : false;
      case DateFilterCondition.NOT_IN_THE_LAST:
        return daysAgo ? mediaDate < daysAgo : false;
      case DateFilterCondition.EQUALS:
        return mediaDate.toDateString() === filterDate.toDateString();
      case DateFilterCondition.NOT_EQUALS:
        return mediaDate.toDateString() !== filterDate.toDateString();
      default:
        return true;
    }
  }

  static applyStringFilter(value: string, filterValue: string, condition: StringFilterCondition): boolean {
    switch (condition) {
      case StringFilterCondition.CONTAINS:
        return value.includes(filterValue);
      case StringFilterCondition.NOT_CONTAINS:
        return !value.includes(filterValue);
      case StringFilterCondition.EQUALS:
        return value === filterValue;
      case StringFilterCondition.NOT_EQUALS:
        return value !== filterValue;
      case StringFilterCondition.STARTS_WITH:
        return value.startsWith(filterValue);
      case StringFilterCondition.NOT_STARTS_WITH:
        return !value.startsWith(filterValue);
      case StringFilterCondition.ENDS_WITH:
        return value.endsWith(filterValue);
      case StringFilterCondition.NOT_ENDS_WITH:
        return !value.endsWith(filterValue);
      case StringFilterCondition.IS_EMPTY:
        return value === '';
      case StringFilterCondition.IS_NOT_EMPTY:
        return value !== '';
      default:
        return true;
    }
  }
}

// Counts the FILE entries in a media's file tree (folders are not counted)
function countFilesInTree(node: FileFolderInfo | null): number {
  if (!node) {
    return 0;
  }
  const self = node.type === 'FILE' ? 1 : 0;
  return (node.children || []).reduce((total, child) => total + countFilesInTree(child), self);
}

// Helper function to search file tree
function findInFileTree(node: FileFolderInfo | null, type: 'FILE' | 'FOLDER', filterValue: string, condition: StringFilterCondition): boolean {
  if (!node) {
    return false;
  }
  // Check current node if it matches the type
  if (node.type === type) {
    if (FilterFunctions.applyStringFilter(node.name.toLowerCase(), filterValue.toLowerCase(), condition)) {
      return true;
    }
  }

  // Recursively check children
  for (const child of node.children || []) {
    if (findInFileTree(child, type, filterValue, condition)) {
      return true;
    }
  }

  return false;
}

/**
 * Evaluates a virtual download field against a media item.
 *
 * All fields use ANY semantics over the download rows: the media matches when
 * at least one download matches the condition. Only active downloads
 * (file_exists) count, except download_file_missing, which exists to find
 * media whose trailer file was deleted from disk.
 *
 * Mirrors `_matches_download_filter` in backend/core/base/utils/filters.py.
 */
function applyDownloadFilter(filter: Filter, media: Media): boolean {
  const {filter_by, filter_value, filter_condition} = filter;
  const active = media.downloads.filter((d) => d.file_exists);
  const boolVal = filter_value.toLowerCase() === 'true';
  const numVal = ParserCache.parseNumber(filter_value);
  const numCondition = filter_condition as NumberFilterCondition;

  switch (filter_by) {
    case 'has_downloads':
      return FilterFunctions.applyBooleanFilter(active.length > 0, boolVal);
    case 'download_count':
      return FilterFunctions.applyNumberFilter(active.length, numVal, numCondition);
    case 'download_file_missing':
      return FilterFunctions.applyBooleanFilter(
        media.downloads.some((d) => !d.file_exists),
        boolVal,
      );
    case 'has_unknown_profile_download':
      return FilterFunctions.applyBooleanFilter(
        active.some((d) => !d.profile_id),
        boolVal,
      );
    case 'download_profile':
      return active.some((d) => FilterFunctions.applyNumberFilter(d.profile_id, numVal, numCondition));
    case 'download_resolution':
      return active.some((d) => FilterFunctions.applyNumberFilter(d.resolution, numVal, numCondition));
    case 'download_added_at': {
      const filterDate = ParserCache.parseDate(filter_value);
      const days = parseInt(filter_value);
      const daysAgo = isNaN(days) ? undefined : ParserCache.getDaysAgo(days);
      return active.some((d) =>
        FilterFunctions.applyDateFilter(ParserCache.parseDate(d.added_at as unknown as string), filterDate, filter_condition as DateFilterCondition, daysAgo),
      );
    }
    default:
      return false;
  }
}

// Main filter dispatcher
function applyFilter(filter: Filter, media: Media): boolean {
  const {filter_by, filter_value, filter_condition} = filter;

  // Virtual download fields, ANY semantics over the download rows
  if (downloadFilterKeys.includes(filter_by)) {
    return applyDownloadFilter(filter, media);
  }

  // Virtual field: number of files on disk for this media
  if (filter_by === 'file_count') {
    const numVal = ParserCache.parseNumber(filter_value);
    return FilterFunctions.applyNumberFilter(countFilesInTree(media.files), numVal, filter_condition as NumberFilterCondition);
  }

  // Special handling for file/folder filters
  if (fileFilterKeys.includes(filter_by)) {
    const fileType = filter_by === 'has_file' ? 'FILE' : 'FOLDER';
    return findInFileTree(media.files, fileType, filter_value, filter_condition as StringFilterCondition);
  }

  // General case for media properties
  const value = media[filter_by as keyof Media];

  if (booleanFilterKeys.includes(filter_by)) {
    const boolVal = filter_value.toLowerCase() === 'true';
    return FilterFunctions.applyBooleanFilter(value as boolean, boolVal);
  }

  if (dateFilterKeys.includes(filter_by)) {
    const mediaDate = ParserCache.parseDate(value as string);
    const filterDate = ParserCache.parseDate(filter_value);
    const days = parseInt(filter_value);
    const daysAgo = isNaN(days) ? undefined : ParserCache.getDaysAgo(days);
    return FilterFunctions.applyDateFilter(mediaDate, filterDate, filter_condition as DateFilterCondition, daysAgo);
  }

  if (numberFilterKeys.includes(filter_by)) {
    if (value === null || value === undefined) return false;
    const numVal = ParserCache.parseNumber(filter_value);
    return FilterFunctions.applyNumberFilter(value as number, numVal, filter_condition as NumberFilterCondition);
  }

  if (stringFilterKeys.includes(filter_by)) {
    return FilterFunctions.applyStringFilter(value as string, filter_value, filter_condition as StringFilterCondition);
  }

  return true;
}

function applyCustomFilter(customFilters: CustomFilter[], filter_name: string, media: Media): boolean {
  let customFilter = customFilters.find((f) => f.filter_name === filter_name);
  if (!customFilter) {
    return true;
  }
  // Apply filters until one of them returns false or all are applied
  return customFilter.filters.every((filter) => applyFilter(filter, media));
}

/**
 * Filters a list of media items based on a selected filter option or custom filters.
 *
 * @param allMedia - The complete array of media items to filter.
 * @param selectedFilter - The filter option selected by the user. Can be one of the predefined filter strings
 *   ('all', 'downloaded', 'downloading', 'missing', 'monitored', 'unmonitored', 'movies', 'series') or a custom filter identifier.
 * @param customFilters - An array of custom filter definitions to be used if the selected filter does not match a predefined option.
 * @returns An array of media items that match the selected filter criteria.
 */
export function applySelectedFilter(allMedia: Media[], selectedFilter: string, customFilters: CustomFilter[]): Media[] {
  // Phase 3: downloaded-ness comes from download rows, never a stored
  // mirror flag; 'downloading' reads the computed status, which
  // the media service derives from the runtime in-flight overlay.
  const hasActiveDownload = (media: Media) => media.downloads.some((d) => d.file_exists);
  // Filter the media list by the selected filter option
  return allMedia.filter((media) => {
    switch (selectedFilter) {
      case 'all':
        return true;
      case 'downloaded':
        return hasActiveDownload(media);
      case 'downloading':
        return media.status.toLowerCase() === 'downloading';
      case 'missing':
        return !hasActiveDownload(media);
      case 'monitored':
        return media.monitor;
      case 'unmonitored':
        return !media.monitor && !hasActiveDownload(media);
      case 'unknown_profile':
        // Media with an active download that has no profile assigned
        return media.downloads.some((d) => d.file_exists && d.profile_id === 0);
      case 'movies':
        return media.is_movie && hasActiveDownload(media);
      case 'series':
        return !media.is_movie && hasActiveDownload(media);
      default:
        return applyCustomFilter(customFilters, selectedFilter, media);
    }
  });
}

/**
 * Gets the most recent download date for a media item.
 * Only considers downloads where the file still exists.
 *
 * @param media - The media object containing download information
 * @returns The most recent download date, or null if no downloads with existing files are found
 */
export function getMediaRecentDownloadDate(media: Media): Date | null {
  const downloadDates = media.downloads
    .filter((d) => d.file_exists)
    .map((d) => new Date(d.added_at))
    .sort((d1, d2) => d2.getTime() - d1.getTime());
  return downloadDates.length > 0 ? downloadDates[0] : null;
}

/**
 * Sorts the provided media list in place based on the selected property and sort direction.
 *
 * @param mediaList - The array of `Media` objects to be sorted. The sorting is performed in place.
 * @param selectedSort - The key of the `Media` object to sort by.
 * @param sortAscending - If `true`, sorts in ascending order; if `false`, sorts in descending order.
 *
 * The function handles sorting for properties of type `Date`, `number`, and other types (using string comparison).
 */
export function applySelectedSort(mediaList: Media[], selectedSort: keyof Media, sortAscending: boolean): void {
  // Sort the media list by the selected sort option
  // Sorts the list in place. If sortAscending is false, reverses the list
  mediaList.sort((a, b) => {
    let aVal = a[selectedSort];
    let bVal = b[selectedSort];
    // Special handling for 'downloaded_at' using the downloads array
    if (selectedSort === 'downloaded_at') {
      aVal = getMediaRecentDownloadDate(a) ?? 0;
      bVal = getMediaRecentDownloadDate(b) ?? 0;
    }
    if (aVal instanceof Date && bVal instanceof Date) {
      if (sortAscending) {
        return aVal.getTime() - bVal.getTime();
      }
      return bVal.getTime() - aVal.getTime();
    }
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      if (sortAscending) {
        return aVal - bVal;
      }
      return bVal - aVal;
    }
    if (aVal == null) aVal = '';
    if (bVal == null) bVal = '';
    if (sortAscending) {
      return aVal.toString().localeCompare(bVal.toString());
    }
    return bVal.toString().localeCompare(aVal.toString());
  });
}

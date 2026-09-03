import {Pipe, PipeTransform} from '@angular/core';

@Pipe({
  name: 'displayTitle',
  pure: true,
})
export class DisplayTitlePipe implements PipeTransform {
  /**
   * Formats a raw value as a display title: underscores become spaces,
   * whitespace is collapsed, and each word starts with a capital letter.
   *
   * Default mode lowercases first — for enum-like tokens
   * (e.g. 'NOT_EQUALS' → 'Not Equals', 'has_downloads' → 'Has Downloads').
   *
   * `fieldKey` mode keeps the value's casing (user-defined names like
   * 'HD Movies' stay intact) and drops a trailing '_at' from field keys
   * (e.g. 'added_at' → 'Added', 'Missing w Media' → 'Missing W Media').
   */
  transform(value: string, fieldKey = false): string {
    const base = fieldKey ? value.replace(/_at$/, '') : value.toLowerCase();
    return base
      .replace(/_/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }
}

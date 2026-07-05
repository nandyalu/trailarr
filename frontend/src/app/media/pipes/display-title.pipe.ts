import {Pipe, PipeTransform} from '@angular/core';

@Pipe({name: 'displayTitle', pure: true})
export class DisplayTitlePipe implements PipeTransform {
  /**
   * Formats the given title string by removing the substring '_at',
   * replacing underscores with spaces, and capitalizing each word.
   *
   * @param title - The title string to be formatted.
   * @returns The formatted option string (e.g. 'unknown_profile' → 'Unknown Profile').
   */
  transform(title: string): string {
    return title
      .replace('_at', '')
      .replace(/_/g, ' ')
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
}

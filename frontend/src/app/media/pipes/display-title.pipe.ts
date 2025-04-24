import {Pipe, PipeTransform} from '@angular/core';

@Pipe({name: 'displayTitle', pure: true})
export class DisplayTitlePipe implements PipeTransform {
  /**
   * Formats the given title string by removing the substring '_at' and capitalizing the first letter.
   *
   * @param title - The title string to be formatted.
   * @returns The formatted option string with '_at' removed and the first letter capitalized.
   */
  transform(title: string): string {
    title = title.replace('_at', '');
    return title.charAt(0).toUpperCase() + title.slice(1);
  }
}

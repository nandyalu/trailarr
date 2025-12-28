import {Pipe, PipeTransform} from '@angular/core';

@Pipe({
  name: 'displayTitle',
  pure: true,
})
export class DisplayTitlePipe implements PipeTransform {
  transform(value: string): unknown {
    return value
      .toLowerCase()
      .replace(/_/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }
}

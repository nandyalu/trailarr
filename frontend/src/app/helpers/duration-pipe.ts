import {Pipe, PipeTransform} from '@angular/core';

@Pipe({
  name: 'durationConvert',
  standalone: true,
})
export class DurationConvertPipe implements PipeTransform {
  transform(value: number): string {
    let hours = Math.floor(value / 60);
    let minutes = Math.floor(value % 60);
    if (hours === 0) {
      return minutes + 'm';
    }
    if (minutes === 0) {
      return hours + 'h';
    }
    return hours + 'h ' + minutes + 'm';
  }
}

import {Pipe, PipeTransform} from '@angular/core';

@Pipe({name: 'interval', standalone: true})
export class IntervalPipe implements PipeTransform {
  transform(seconds: number): string {
    const timeUnits = [
      {unit: 'second', value: 60},
      {unit: 'minute', value: 60},
      {unit: 'hour', value: 24},
      {unit: 'day', value: 7},
    ];

    for (const {unit, value} of timeUnits) {
      if (seconds < value) {
        return `${seconds} ${unit}${seconds === 1 ? '' : 's'}`;
      }
      seconds = Math.floor(seconds / value);
    }
    return `${seconds} ${seconds === 1 ? 'week' : 'weeks'}`;
  }
}

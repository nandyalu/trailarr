import {Pipe, PipeTransform} from '@angular/core';

@Pipe({name: 'duration', standalone: true})
export class DurationPipe implements PipeTransform {
  transform(seconds: number | null | undefined, fallback = ''): string {
    if (seconds === null || seconds === undefined) return fallback;
    if (seconds < 1) return '00:00:00';
    const h = Math.floor(seconds / 3600)
      .toString()
      .padStart(2, '0');
    const m = Math.floor((seconds % 3600) / 60)
      .toString()
      .padStart(2, '0');
    const s = Math.floor(seconds % 60)
      .toString()
      .padStart(2, '0');
    return `${h}:${m}:${s}`;
  }
}

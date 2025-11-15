import {Pipe, PipeTransform} from '@angular/core';
import {distinctUntilChanged, interval, map, Observable, startWith} from 'rxjs';

export const msSecond = 1000;
export const msMinute = 60 * msSecond;
export const msHour = 60 * msMinute;
export const msDay = 24 * msHour;

@Pipe({
  name: 'timediff',
  pure: false,
  standalone: true, // Add this for Angular standalone components
})
export class TimediffPipe implements PipeTransform {
  transform(value: string | number | Date | null | undefined, invalidReturn: string = 'Invalid date'): Observable<string> {
    if (!value) {
      // If value is null or undefined, return an observable that emits invalidReturn
      return new Observable((subscriber) => {
        subscriber.next(invalidReturn);
        subscriber.complete();
      });
    }

    return interval(1000).pipe(
      startWith(0),
      map(() => this.getTimeDifferenceString(value, invalidReturn)),
      distinctUntilChanged(),
    );
  }

  private getTimeDifferenceString(value: string | number | Date | null | undefined, invalidReturn: string = 'Invalid date'): string {
    if (!value) {
      return invalidReturn;
    }

    const date = new Date(value);
    if (isNaN(date.getTime())) {
      console.log('Invalid date in TimediffPipe:', value);
      return invalidReturn;
    }

    const now = new Date();
    let diffMs = now.getTime() - date.getTime();

    const suffix = diffMs < 0 ? 'from now' : 'ago';
    diffMs = Math.abs(diffMs);

    // Calculate time units and return result early
    const days = Math.floor(diffMs / msDay);
    if (days > 0) {
      return `${days} day${days !== 1 ? 's' : ''} ${suffix}`;
    }
    const hours = Math.floor((diffMs % msDay) / msHour);
    if (hours > 0) {
      return `${hours} hour${hours !== 1 ? 's' : ''} ${suffix}`;
    }
    const minutes = Math.floor((diffMs % msHour) / msMinute);
    if (minutes > 0) {
      return `${minutes} minute${minutes !== 1 ? 's' : ''} ${suffix}`;
    }
    const seconds = Math.floor((diffMs % msMinute) / msSecond);
    return `${seconds} second${seconds !== 1 ? 's' : ''} ${suffix}`;
  }
}

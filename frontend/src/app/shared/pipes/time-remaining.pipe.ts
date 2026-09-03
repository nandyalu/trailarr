import {Pipe, PipeTransform} from '@angular/core';
import {Observable, interval, map, startWith} from 'rxjs';
import {timeRemainingString} from 'src/util';

@Pipe({
  name: 'timeRemaining',
  pure: true,
})
export class TimeRemainingPipe implements PipeTransform {
  transform(value: number | Date): Observable<string> {
    const getMillis = () => (typeof value === 'number' ? value : value instanceof Date ? value.getTime() : null);
    return interval(1000).pipe(
      startWith(0),
      map(() => {
        const millis = getMillis();
        if (millis === null) return 'Invalid date';
        return timeRemainingString(millis);
      }),
    );
  }
}

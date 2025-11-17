import {Pipe, PipeTransform} from '@angular/core';
import {durationStringSeconds} from 'src/util';

@Pipe({name: 'durationSecondsConvert', pure: true})
export class DurationSecondsConvertPipe implements PipeTransform {
  transform(value: number) {
    return durationStringSeconds(value);
  }
}

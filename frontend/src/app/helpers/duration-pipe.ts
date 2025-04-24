import {Pipe, PipeTransform} from '@angular/core';
import {durationString} from 'src/util';

@Pipe({name: 'durationConvert', pure: true})
export class DurationConvertPipe implements PipeTransform {
  transform(value: number) {
    return durationString(value);
  }
}

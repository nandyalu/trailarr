import {Pipe, PipeTransform} from '@angular/core';
import {bytesToSize} from 'src/util';

@Pipe({name: 'fileSize', pure: true})
export class FileSizePipe implements PipeTransform {
  transform(value: number): string {
    return bytesToSize(value);
  }
}

import {Pipe, PipeTransform} from '@angular/core';

@Pipe({
  name: 'removeStartingSlash',
  standalone: true,
})
export class RemoveStartingSlashPipe implements PipeTransform {
  transform(value: string | null | undefined): string | null | undefined {
    if (value && value.startsWith('/')) {
      return value.substring(1);
    }
    return value;
  }
}

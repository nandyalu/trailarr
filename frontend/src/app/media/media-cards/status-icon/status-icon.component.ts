import {Component, input} from '@angular/core';

@Component({
  selector: 'media-status-icon',
  imports: [],
  templateUrl: './status-icon.component.html',
  styleUrl: './status-icon.component.scss',
})
export class StatusIconComponent {
  status = input.required<string>();
}

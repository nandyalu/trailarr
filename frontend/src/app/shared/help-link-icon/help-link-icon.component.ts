import {ChangeDetectionStrategy, Component, input} from '@angular/core';

@Component({
  selector: 'help-link-icon',
  imports: [],
  templateUrl: './help-link-icon.component.html',
  styleUrl: './help-link-icon.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HelpLinkIconComponent {
  link = input.required<string>();

  openExternalLink(event?: Event) {
    event?.preventDefault();
    window.open(this.link(), '_blank', 'noopener');
  }
}

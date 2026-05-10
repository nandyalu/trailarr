import {ChangeDetectionStrategy, Component, computed, input, output} from '@angular/core';
import {RouterLink} from '@angular/router';
import {Media} from 'src/app/models/media';
import {RouteMedia} from 'src/routing';
import {StatusIconComponent} from '../status-icon/status-icon.component';

@Component({
  selector: 'app-media-card-shell',
  imports: [RouterLink, StatusIconComponent],
  templateUrl: './media-card-shell.component.html',
  styleUrl: './media-card-shell.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  host: {
    class: 'media-card',
    role: 'option',
    '[attr.aria-selected]': 'inEditMode() && isChecked()',
    '[attr.title]': 'cardTitle()',
  },
})
export class MediaCardShellComponent {
  readonly media = input.required<Media>();
  readonly inEditMode = input.required<boolean>();
  readonly isChecked = input.required<boolean>();
  readonly checkedChange = output<boolean>();
  readonly cardClicked = output<void>();

  protected readonly RouteMedia = RouteMedia;
  protected readonly checkboxId = computed(() => `card-${this.media().id}`);
  protected readonly cardTitle = computed(() => {
    const m = this.media();
    const status = m.status.charAt(0).toUpperCase() + m.status.slice(1);
    return `${m.title} (${status})`;
  });
}

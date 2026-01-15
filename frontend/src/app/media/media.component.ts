import {ChangeDetectionStrategy, Component, effect, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Router, RouterState} from '@angular/router';
import {CustomfilterService} from '../services/customfilter.service';
import {MediaService} from '../services/media.service';
import {LoadIndicatorComponent} from '../shared/load-indicator';
import {EditHeaderComponent} from './headers/edit-header/edit-header.component';
import {NormalHeaderComponent} from './headers/normal-header/normal-header.component';
import {PosterComponent} from './media-cards/poster/poster.component';

@Component({
  selector: 'app-media',
  imports: [EditHeaderComponent, FormsModule, LoadIndicatorComponent, NormalHeaderComponent, PosterComponent],
  templateUrl: './media.component.html',
  styleUrl: './media.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MediaComponent implements OnInit {
  private readonly customfilterService = inject(CustomfilterService);
  private readonly mediaService = inject(MediaService);
  private readonly router = inject(Router);

  // Signals from Media Service
  protected readonly moviesOnly = this.mediaService.moviesOnly;
  protected readonly filteredSortedMedia = this.mediaService.filteredSortedMedia;
  protected readonly inEditMode = this.mediaService.inEditMode;

  // Signals in this component
  protected readonly isLoading = signal<boolean>(true);

  ngOnInit() {
    this.isLoading.set(true);
    const state: RouterState = this.router.routerState;
    const currentRoute = state.snapshot.url.toLowerCase();
    // let type = this.route.snapshot.url[0].path;
    switch (currentRoute) {
      case '/movies':
        this.moviesOnly.set(true);
        break;
      case '/series':
        this.moviesOnly.set(false);
        break;
      default:
        this.moviesOnly.set(null);
    }
  }

  // Effects for reacting to changes
  effect1 = effect(() => {
    let mediaList = this.mediaService.mediaResource.value();
    if (mediaList.length) {
      this.isLoading.set(false);
    }
    if (!this.mediaService.mediaResource.isLoading()) {
      this.isLoading.set(false);
    }
    this.customfilterService.moviesOnly.set(this.moviesOnly());
  });
}

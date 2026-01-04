import {NgTemplateOutlet} from '@angular/common';
import {ChangeDetectionStrategy, Component, effect, inject, OnInit, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Router, RouterLink, RouterState} from '@angular/router';
import {RouteMedia} from 'src/routing';
import {ScrollNearEndDirective} from '../helpers/scroll-near-end-directive';
import {Media} from '../models/media';
import {CustomfilterService} from '../services/customfilter.service';
import {MediaService} from '../services/media.service';
import {LoadIndicatorComponent} from '../shared/load-indicator';
import {EditHeaderComponent} from './headers/edit-header/edit-header.component';
import {NormalHeaderComponent} from './headers/normal-header/normal-header.component';

@Component({
  selector: 'app-media2',
  imports: [
    EditHeaderComponent,
    FormsModule,
    NgTemplateOutlet,
    LoadIndicatorComponent,
    NormalHeaderComponent,
    RouterLink,
    ScrollNearEndDirective,
  ],
  templateUrl: './media.component.html',
  styleUrl: './media.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MediaComponent implements OnInit {
  private readonly customfilterService = inject(CustomfilterService);
  private readonly mediaService = inject(MediaService);
  private readonly router = inject(Router);

  // Signals from Media Service
  protected readonly checkedMediaIDs = this.mediaService.checkedMediaIDs;
  protected readonly displayCount = this.mediaService.displayCount;
  protected readonly displayMedia = this.mediaService.displayMedia;
  protected readonly filteredSortedMedia = this.mediaService.filteredSortedMedia;
  protected readonly inEditMode = this.mediaService.inEditMode;
  protected readonly moviesOnly = this.mediaService.moviesOnly;

  // Signals in this component
  protected readonly isLoading = signal<boolean>(true);
  protected readonly navigatingMediaId = this.mediaService.selectedMediaID;

  // Constants
  protected readonly defaultDisplayCount = this.mediaService.defaultDisplayCount;
  protected readonly RouteMedia = RouteMedia;

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

  /**
   * Handles the event when a media item is selected, either by checking or unchecking a checkbox.
   * Adds or removes the media item from the selectedMedia array based on the checkbox state.
   *
   * @param {Media} media - The media item that was selected.
   * @param {Event} event - The event that triggered the selection.
   * @returns {void}
   */
  onMediaSelected(media: Media, event: Event): void {
    // Navigate to the media details page
    const inputElement = event.target as HTMLInputElement;
    if (inputElement.checked) {
      this.checkedMediaIDs.update((ids) => [...ids, media.id]);
    } else {
      this.checkedMediaIDs.update((ids) => ids.filter((id) => id !== media.id));
    }
  }

  /**
   * Handles the event when the user scrolls near the end of the media list.
   * Loads more media items into the display list if there are more items to show.
   *
   * @returns {void} This method does not return a value.
   */
  onNearEndScroll(): void {
    // Load more media when near the end of the scroll
    if (this.displayCount() >= this.filteredSortedMedia().length) {
      return;
    }
    this.displayCount.update((count) => count + this.defaultDisplayCount);
  }

  onMediaClick(mediaId: number): void {
    this.navigatingMediaId.set(mediaId);
  }
}

import {httpResource} from '@angular/common/http';
import {ChangeDetectionStrategy, Component, computed, effect, ElementRef, inject, OnInit, signal, viewChild} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Router, RouterLink, RouterState} from '@angular/router';
import {environment} from '../../environment';
import {mapPendingSummary, PendingSummary} from '../models/pending';
import {CustomfilterService} from '../services/customfilter.service';
import {MediaService} from '../services/media.service';
import {SettingsService} from '../services/settings.service';
import {LoadIndicatorComponent} from '../shared/load-indicator';
import {EditHeaderComponent} from './headers/edit-header/edit-header.component';
import {NormalHeaderComponent} from './headers/normal-header/normal-header.component';
import {ExpandedComponent} from './media-cards/expanded/expanded.component';
import {PosterComponent} from './media-cards/poster/poster.component';
import {TableComponent} from './media-cards/table/table.component';

@Component({
  selector: 'app-media',
  imports: [EditHeaderComponent, ExpandedComponent, FormsModule, LoadIndicatorComponent, NormalHeaderComponent, PosterComponent, RouterLink, TableComponent],
  templateUrl: './media.component.html',
  styleUrl: './media.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MediaComponent implements OnInit {
  private readonly customfilterService = inject(CustomfilterService);
  private readonly mediaService = inject(MediaService);
  private readonly settingsService = inject(SettingsService);
  private readonly router = inject(Router);

  // Signals from Media Service
  protected readonly moviesOnly = this.mediaService.moviesOnly;
  protected readonly filteredSortedMedia = this.mediaService.filteredSortedMedia;
  protected readonly inEditMode = this.mediaService.inEditMode;
  protected readonly selectedView = this.mediaService.selectedView;
  protected readonly unknownProfileCount = this.mediaService.unknownProfileCount;
  protected readonly selectedFilter = this.mediaService.selectedFilter;

  // Signals in this component
  protected readonly isLoading = signal<boolean>(true);

  /** Preview mode (Phase 3): automatic downloads are disabled — show the
   * banner with the would-download list. */
  protected readonly previewMode = computed(() => this.settingsService.settingsResource.value()?.downloads_enabled === false);
  protected readonly pendingSummaryResource = httpResource<PendingSummary | null>(
    () => (this.previewMode() ? {url: environment.apiUrl + environment.media + 'pending', params: {limit: 500}} : undefined),
    {
      defaultValue: null,
      parse: (response) => (response ? mapPendingSummary(response) : null),
    },
  );
  private readonly previewDialog = viewChild<ElementRef<HTMLDialogElement>>('previewDialog');

  protected openPreviewDialog() {
    this.pendingSummaryResource.reload();
    this.previewDialog()?.nativeElement.showModal();
  }

  protected closePreviewDialog() {
    this.previewDialog()?.nativeElement.close();
  }

  /** Applies the 'Unknown Profile' quick filter from the review banner */
  protected reviewUnknownProfiles() {
    this.mediaService.selectedFilter.set('unknown_profile');
  }

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

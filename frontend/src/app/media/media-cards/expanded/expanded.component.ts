import {DatePipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, inject} from '@angular/core';
import {RemoveStartingSlashPipe} from 'src/app/shared/pipes/remove-starting-slash.pipe';
import {ScrollNearEndDirective} from 'src/app/shared/directives/scroll-near-end-directive';
import {Download, Media} from 'src/app/models/media';
import {
  buildTrailerBlock,
  FieldContext,
  FieldDef,
  isTrailerField,
  MediaFieldDef,
  mediaTagValue,
  resolveFields,
  TrailerBlock,
  TrailerFieldDef,
} from 'src/app/media/utils/media-fields';
import {MediaService} from 'src/app/services/media.service';
import {ProfileService} from 'src/app/services/profile.service';
import {MediaCardShellComponent} from '../media-card-shell/media-card-shell.component';

/** The fields the title line and the overview paragraph place themselves. */
const PLACED_FIELDS = ['year', 'overview'];

@Component({
  selector: 'media-expanded-card',
  imports: [DatePipe, MediaCardShellComponent, RemoveStartingSlashPipe, ScrollNearEndDirective],
  templateUrl: './expanded.component.html',
  styleUrl: './expanded.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ExpandedComponent {
  private readonly mediaService = inject(MediaService);
  private readonly profileService = inject(ProfileService);

  protected readonly checkedMediaIDs = this.mediaService.checkedMediaIDs;
  protected readonly defaultDisplayCount = this.mediaService.defaultDisplayCount;
  protected readonly displayCount = this.mediaService.displayCount;
  protected readonly displayMedia = this.mediaService.displayMedia;
  protected readonly filteredSortedMedia = this.mediaService.filteredSortedMedia;
  protected readonly inEditMode = this.mediaService.inEditMode;
  protected readonly selectedMediaID = this.mediaService.selectedMediaID;
  protected readonly expandedFields = this.mediaService.expandedFields;

  protected readonly onMediaChecked = this.mediaService.onMediaChecked.bind(this.mediaService);

  /** The saved field keys, resolved against the field registry. A key the
   * registry does not know is dropped. */
  private readonly activeFields = computed(() => resolveFields(this.expandedFields(), 'expanded'));

  /** The media fields shown as tags, in the registry order. */
  protected readonly mediaTagFields = computed(() =>
    this.activeFields().filter((f): f is MediaFieldDef => f.group === 'media' && !PLACED_FIELDS.includes(f.key)),
  );

  /** The trailer fields shown in one row of tags per trailer. */
  protected readonly trailerTagFields = computed(() =>
    this.activeFields().filter((f): f is TrailerFieldDef => isTrailerField(f) && !f.summary),
  );

  /** True when the trailer count is on. It shows as one media tag, because
   * it belongs to the media item and not to one trailer. */
  protected readonly showTrailerCount = computed(() => this.activeFields().some((f) => isTrailerField(f) && f.summary));

  /** Profile id -> name, for the Profile tag. */
  protected readonly fieldContext = computed<FieldContext>(() => ({
    profileNames: new Map(this.profileService.allProfiles.value().map((p) => [p.id, p.customfilter.filter_name])),
  }));

  /** One trailer order per shown media item, computed once per item. */
  private readonly trailerBlocks = computed(() => {
    const blocks = new Map<number, TrailerBlock>();
    if (this.trailerTagFields().length === 0 && !this.showTrailerCount()) return blocks;
    for (const media of this.displayMedia()) {
      blocks.set(media.id, buildTrailerBlock(media));
    }
    return blocks;
  });

  protected hasField(field: string): boolean {
    return this.expandedFields().includes(field);
  }

  protected getTagValue(field: MediaFieldDef, media: Media): string | null {
    return mediaTagValue(field, media);
  }

  protected getDateValue(field: FieldDef, media: Media): Date | null {
    return field.group === 'media' && field.date ? field.date(media) : null;
  }

  protected getTrailerBlock(media: Media): TrailerBlock {
    return this.trailerBlocks().get(media.id) ?? buildTrailerBlock(media);
  }

  protected getTrailerValue(field: TrailerFieldDef, trailer: Download): string {
    return field.value(trailer, this.fieldContext());
  }

  onNearEndScroll(): void {
    if (this.displayCount() >= this.filteredSortedMedia().length) return;
    this.displayCount.update((count) => count + this.defaultDisplayCount);
  }
}

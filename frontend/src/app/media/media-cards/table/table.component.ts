import {DatePipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, inject} from '@angular/core';
import {RouterLink} from '@angular/router';
import {DisplayTitlePipe} from 'src/app/shared/pipes/display-title.pipe';
import {ScrollNearEndDirective} from 'src/app/shared/directives/scroll-near-end-directive';
import {Media} from 'src/app/models/media';
import {
  buildTrailerBlock,
  EMPTY_VALUE,
  FieldContext,
  FieldDef,
  headerLabel,
  isTrailerField,
  mediaCellValue,
  resolveFields,
  TrailerBlock,
  trailerCellLines,
} from 'src/app/media/utils/media-fields';
import {MediaService} from 'src/app/services/media.service';
import {ProfileService} from 'src/app/services/profile.service';
import {RouteMedia} from 'src/routing';
import {StatusIconComponent} from '../status-icon/status-icon.component';

@Component({
  selector: 'media-table-view',
  imports: [DatePipe, DisplayTitlePipe, RouterLink, ScrollNearEndDirective, StatusIconComponent],
  templateUrl: './table.component.html',
  styleUrl: './table.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TableComponent {
  private readonly mediaService = inject(MediaService);
  private readonly profileService = inject(ProfileService);

  protected readonly checkedMediaIDs = this.mediaService.checkedMediaIDs;
  protected readonly defaultDisplayCount = this.mediaService.defaultDisplayCount;
  protected readonly displayCount = this.mediaService.displayCount;
  protected readonly displayMedia = this.mediaService.displayMedia;
  protected readonly filteredSortedMedia = this.mediaService.filteredSortedMedia;
  protected readonly inEditMode = this.mediaService.inEditMode;
  protected readonly selectedMediaID = this.mediaService.selectedMediaID;
  protected readonly tableColumns = this.mediaService.tableColumns;

  protected readonly onMediaChecked = this.mediaService.onMediaChecked.bind(this.mediaService);
  protected readonly RouteMedia = RouteMedia;
  protected readonly EMPTY_VALUE = EMPTY_VALUE;
  protected readonly headerLabel = headerLabel;

  /** The saved column keys, resolved against the field registry. A key the
   * registry does not know is dropped. */
  protected readonly activeColumns = computed(() => resolveFields(this.tableColumns(), 'table'));

  private readonly hasTrailerColumns = computed(() => this.activeColumns().some(isTrailerField));

  /** Profile id -> name, for the Trailer Profile column. */
  private readonly fieldContext = computed<FieldContext>(() => ({
    profileNames: new Map(this.profileService.allProfiles.value().map((p) => [p.id, p.customfilter.filter_name])),
  }));

  /** One trailer order per shown media item, computed once and read by
   * every trailer cell, so the stacked lines align across the columns. */
  private readonly trailerBlocks = computed(() => {
    const blocks = new Map<number, TrailerBlock>();
    if (!this.hasTrailerColumns()) return blocks;
    for (const media of this.displayMedia()) {
      blocks.set(media.id, buildTrailerBlock(media));
    }
    return blocks;
  });

  onNearEndScroll(): void {
    if (this.displayCount() >= this.filteredSortedMedia().length) return;
    this.displayCount.update((count) => count + this.defaultDisplayCount);
  }

  protected isDateColumn(field: FieldDef): boolean {
    return field.group === 'media' && field.date !== undefined;
  }

  protected getDateValue(field: FieldDef, media: Media): Date | null {
    return field.group === 'media' && field.date ? field.date(media) : null;
  }

  protected getCellValue(field: FieldDef, media: Media): string {
    if (isTrailerField(field)) return EMPTY_VALUE;
    return mediaCellValue(field, media) ?? EMPTY_VALUE;
  }

  /** The stacked lines of a trailer cell: one per shown trailer, or the
   * summary for the count field. Empty when there is no active download. */
  protected getTrailerLines(field: FieldDef, media: Media): string[] {
    if (!isTrailerField(field)) return [];
    const block = this.trailerBlocks().get(media.id) ?? buildTrailerBlock(media);
    return trailerCellLines(field, block, this.fieldContext());
  }

  /** How many trailers the cap hides in this cell. Zero for the count field. */
  protected getTrailerMore(field: FieldDef, media: Media): number {
    if (!isTrailerField(field) || field.summary) return 0;
    return this.trailerBlocks().get(media.id)?.more ?? 0;
  }

  protected checkAll(checked: boolean): void {
    if (checked) {
      this.checkedMediaIDs.set(this.filteredSortedMedia().map((m) => m.id));
    } else {
      this.checkedMediaIDs.set([]);
    }
  }
}

import {DatePipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, inject} from '@angular/core';
import {RouterLink} from '@angular/router';
import {DisplayTitlePipe} from 'src/app/helpers/display-title.pipe';
import {DurationConvertPipe} from 'src/app/helpers/duration-pipe';
import {ScrollNearEndDirective} from 'src/app/helpers/scroll-near-end-directive';
import {Media} from 'src/app/models/media';
import {MediaService} from 'src/app/services/media.service';
import {RouteMedia} from 'src/routing';
import {StatusIconComponent} from '../status-icon/status-icon.component';

@Component({
  selector: 'media-table-view',
  imports: [DatePipe, DisplayTitlePipe, DurationConvertPipe, RouterLink, ScrollNearEndDirective, StatusIconComponent],
  templateUrl: './table.component.html',
  styleUrl: './table.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TableComponent {
  private readonly mediaService = inject(MediaService);

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

  readonly allColumnDefs: {key: string; label: string}[] = [
    {key: 'year', label: 'Year'},
    {key: 'status', label: 'Status'},
    {key: 'runtime', label: 'Runtime'},
    {key: 'language', label: 'Language'},
    {key: 'studio', label: 'Studio'},
    {key: 'season_count', label: 'Seasons'},
    {key: 'monitor', label: 'Monitored'},
    {key: 'arr_monitored', label: 'Arr Monitored'},
    {key: 'media_exists', label: 'Media Exists'},
    {key: 'trailer_exists', label: 'Trailer Exists'},
    {key: 'imdb_id', label: 'IMDB ID'},
    {key: 'tmdb_id', label: 'TMDB ID'},
    {key: 'tvdb_id', label: 'TVDB ID'},
    {key: 'folder_path', label: 'Folder Path'},
    {key: 'media_filename', label: 'Filename'},
    {key: 'added_at', label: 'Date Added'},
    {key: 'updated_at', label: 'Date Updated'},
    {key: 'downloaded_at', label: 'Date Downloaded'},
    {key: 'plex_rating_key', label: 'Plex Rating Key'},
    {key: 'plex_trailer', label: 'Plex Trailer'},
  ];

  protected readonly activeColumns = computed(() => {
    const keys = this.tableColumns();
    return keys
      .map((k) => this.allColumnDefs.find((d) => d.key === k))
      .filter((d): d is {key: string; label: string} => d !== undefined);
  });

  onNearEndScroll(): void {
    if (this.displayCount() >= this.filteredSortedMedia().length) return;
    this.displayCount.update((count) => count + this.defaultDisplayCount);
  }

  protected isDateColumn(key: string): boolean {
    return key === 'added_at' || key === 'updated_at' || key === 'downloaded_at';
  }

  protected isRuntimeColumn(key: string): boolean {
    return key === 'runtime';
  }

  protected getDateValue(media: Media, key: string): Date | null {
    if (key === 'added_at') return media.added_at;
    if (key === 'updated_at') return media.updated_at;
    if (key === 'downloaded_at') return media.downloaded_at;
    return null;
  }

  protected getCellValue(media: Media, key: string): string {
    switch (key) {
      case 'year':          return media.year ? String(media.year) : '—';
      case 'status':        return media.status ? media.status.charAt(0).toUpperCase() + media.status.slice(1) : '—';
      case 'language':      return media.language || '—';
      case 'studio':        return media.studio || '—';
      case 'season_count':  return media.is_movie ? '—' : (media.season_count ? String(media.season_count) : '—');
      case 'monitor':       return media.monitor ? 'Yes' : 'No';
      case 'arr_monitored': return media.arr_monitored ? 'Yes' : 'No';
      case 'media_exists':  return media.media_exists ? 'Yes' : 'No';
      case 'trailer_exists': return media.trailer_exists ? 'Yes' : 'No';
      case 'imdb_id':       return media.imdb_id || '—';
      case 'tmdb_id':       return media.tmdb_id || '—';
      case 'tvdb_id':       return media.tvdb_id || '—';
      case 'folder_path':   return media.folder_path || '—';
      case 'media_filename': return media.media_filename || '—';
      case 'plex_rating_key': return media.plex_rating_key || '—';
      case 'plex_trailer':  return media.plex_trailer === null ? '—' : media.plex_trailer ? 'Yes' : 'No';
      default:              return '—';
    }
  }

  protected checkAll(checked: boolean): void {
    if (checked) {
      this.checkedMediaIDs.set(this.filteredSortedMedia().map((m) => m.id));
    } else {
      this.checkedMediaIDs.set([]);
    }
  }
}

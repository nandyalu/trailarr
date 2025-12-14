import {DatePipe, NgTemplateOutlet} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, effect, inject, input, resource, signal} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormsModule} from '@angular/forms';
import {FilesService} from 'generated-sources/openapi';

import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {FolderInfo} from '../../../models/media';
import {MediaService} from '../../../services/media.service';
import {WebsocketService} from '../../../services/websocket.service';
import {OptionsDialogComponent} from './dialogs/options-dialog/options-dialog.component';

interface ErrorMessage {
  error: {
    detail: string;
  };
}

@Component({
  selector: 'media-files',
  imports: [DatePipe, FormsModule, LoadIndicatorComponent, NgTemplateOutlet, OptionsDialogComponent],
  templateUrl: './files.component.html',
  styleUrl: './files.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FilesComponent {
  private readonly filesService = inject(FilesService);
  private readonly mediaService = inject(MediaService);
  private readonly webSocketService = inject(WebsocketService);

  readonly mediaId = input.required<number>();

  protected readonly filesOpened = signal(false);
  protected readonly optionsDialogOpen = signal(false);
  // mediaFilesResponse: string = 'No files found';
  // mediaFiles: FolderInfo | undefined = undefined;

  mediaIDEffect = effect(() => {
    this.mediaId();
    this.filesOpened.set(false); // Reset filesOpened when mediaId changes
  });

  selectedFilePath = signal('');
  protected readonly selectedFileName = signal('');



  // Refresh the files list when the mediaId changes and filesOpened is true
  protected readonly filesResource = resource({
    params: () => ({mediaId: this.mediaId(), filesOpened: this.filesOpened()}),
    loader: async ({params: {mediaId, filesOpened}}) => {
      if (!filesOpened) return undefined;
      return await this.mediaService.fetchMediaFiles(mediaId);
    },
  });

  protected readonly filesError = computed(() => {
    const _error = this.filesResource.error();
    if (!_error) return '';
    const cause = _error.cause as ErrorMessage;
    return cause?.error.detail || 'Error fetching media files.';
  });



  ngOnInit() {
    // Subscribe to WebSocket updates to reload media data when necessary
    this.webSocketService.toastMessage.pipe(takeUntilDestroyed()).subscribe((msg) => {
      const msgText = msg.message.toLowerCase();
      const mediaIdStr = this.mediaId().toString();
      const mediaTitle = this.mediaService.selectedMedia()?.title?.toLowerCase() || '';
      const checkForItems = ['media', 'trailer', mediaIdStr, mediaTitle];
      if (checkForItems.some((term) => term && msgText.includes(term))) {
        this.filesResource.reload();
      }
    });
  }

  asFolderInfo(folder: FolderInfo): FolderInfo {
    // For use in ng-template for type checking
    return folder;
  }

  openFolderOrOptions(folder: FolderInfo): void {
    if (folder.type === 'folder') {
      folder.isExpanded = !folder.isExpanded;
    } else {
      this.selectedFilePath.set(folder.path);
      this.selectedFileName.set(folder.name);
      this.openOptionsDialog();
    }
  }

  openOptionsDialog(): void {
    this.optionsDialogOpen.set(true);
  }

  onOptionsDialogClosed(): void {
    this.optionsDialogOpen.set(false);
  }

  onFilesRefreshed(): void {
    this.filesResource.reload();
  }
}

import {DatePipe, NgTemplateOutlet} from '@angular/common';
import {ChangeDetectionStrategy, Component, inject, input, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';

import {FileSizePipe} from 'src/app/helpers/file-size.pipe';
import {FileFolderInfo} from 'src/app/models/filefolderinfo';
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
  imports: [DatePipe, FileSizePipe, FormsModule, NgTemplateOutlet, OptionsDialogComponent],
  templateUrl: './files.component.html',
  styleUrl: './files.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FilesComponent {
  private readonly mediaService = inject(MediaService);
  private readonly webSocketService = inject(WebsocketService);

  readonly mediaId = input.required<number>();

  protected readonly isLoading = signal(false);
  protected readonly optionsDialogOpen = signal(false);
  protected readonly media = this.mediaService.selectedMedia;

  // mediaFilesResponse: string = 'No files found';
  // mediaFiles: FolderInfo | undefined = undefined;

  selectedFilePath = signal('');
  protected readonly selectedFileName = signal('');

  asFolderInfo(folder: FileFolderInfo): FileFolderInfo {
    // For use in ng-template for type checking
    return folder;
  }

  openFolderOrOptions(folder: FileFolderInfo): void {
    if (folder.type === 'FOLDER') {
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

  rescanMediaFiles(): void {
    this.isLoading.set(true);
    this.mediaService.rescanMediaFiles(this.mediaId()).subscribe(() => {
      this.isLoading.set(false);
      this.webSocketService.showToast('Media files rescanned successfully.', 'success');
      this.mediaService.refreshContent();
    });
  }
}

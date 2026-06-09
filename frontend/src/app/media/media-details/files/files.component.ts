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

  protected expandAll(): void {
    const files = this.media()?.files;
    if (files) this.setExpanded(files, true);
  }

  protected collapseAll(): void {
    const files = this.media()?.files;
    if (files) this.setExpanded(files, false);
  }

  private setExpanded(node: FileFolderInfo, expanded: boolean): void {
    if (node.type === 'FOLDER') {
      node.isExpanded = expanded;
      node.children.forEach((child) => this.setExpanded(child, expanded));
    }
  }

  protected getIconClass(file: FileFolderInfo): string {
    if (file.type === 'FOLDER') return 'icon-folder';
    const ext = file.name.split('.').pop()?.toLowerCase() ?? '';
    if (['mp4', 'mkv', 'avi', 'webm', 'mov'].includes(ext)) return 'icon-video';
    if (['srt', 'txt', 'log', 'json', 'vtt', 'ass'].includes(ext)) return 'icon-text';
    return 'icon-other';
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

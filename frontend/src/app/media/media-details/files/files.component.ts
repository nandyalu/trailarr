import {DatePipe, NgTemplateOutlet} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, effect, ElementRef, inject, input, resource, signal, ViewChild} from '@angular/core';
import {takeUntilDestroyed} from '@angular/core/rxjs-interop';
import {FormsModule} from '@angular/forms';
import {FilesService, VideoInfo} from 'generated-sources/openapi';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {jsonEqual} from 'src/util';
import {FolderInfo} from '../../../models/media';
import {MediaService} from '../../../services/media.service';
import {WebsocketService} from '../../../services/websocket.service';

interface ErrorMessage {
  error: {
    detail: string;
  };
}

@Component({
  selector: 'media-files',
  imports: [DatePipe, FormsModule, LoadIndicatorComponent, NgTemplateOutlet],
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
  protected readonly textFileLoading = signal(true);
  protected readonly videoInfoLoading = signal(true);
  // mediaFilesResponse: string = 'No files found';
  // mediaFiles: FolderInfo | undefined = undefined;

  mediaIDEffect = effect(() => {
    this.mediaId();
    this.filesOpened.set(false); // Reset filesOpened when mediaId changes
  });

  selectedFilePath: string = '';
  protected readonly selectedFileName = signal('');
  protected readonly videoInfo = signal<VideoInfo | null>(null);
  protected readonly selectedFileText = signal<string[]>([], {equal: jsonEqual});

  protected readonly audioTracks = computed(() =>
    (this.videoInfo()?.streams ?? [])
      .filter((stream) => stream.codec_type.includes('audio'))
      .map((stream) => `${stream.language || 'unk'} (${stream.codec_name})`)
      .join(', '),
  );

  protected readonly subtitleTracks = computed(() =>
    (this.videoInfo()?.streams ?? [])
      .filter((stream) => stream.codec_type.includes('subtitle'))
      .map((stream) => `${stream.language || 'unk'} (${stream.codec_name})`)
      .join(', '),
  );

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

  protected readonly isTextFile = computed(() =>
    ['.txt', '.srt', '.log', '.json', '.py', '.sh'].some((ext) => this.selectedFileName().endsWith(ext)),
  );

  protected readonly isVideoFile = computed(() => ['.mp4', '.mkv', '.avi', '.webm'].some((ext) => this.selectedFileName().endsWith(ext)));

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
      this.selectedFilePath = folder.path;
      this.selectedFileName.set(folder.name);
      this.openOptionsDialog();
    }
  }

  renameFile(): void {
    this.closeRenameDialog();
    let selectedFileBasePath = this.selectedFilePath.split('/').slice(0, -1).join('/');
    let newName = selectedFileBasePath + '/' + this.selectedFileName();
    this.filesService.renameFileFolApiV1FilesRenamePost({old_path: this.selectedFilePath, new_path: newName}).subscribe((renamed) => {
      // Display the return message
      let msg: string = '';
      if (renamed) {
        msg = 'File renamed successfully!';
      } else {
        msg = 'Failed to rename file!';
      }
      this.webSocketService.showToast(msg, renamed ? 'success' : 'error');
      // Refresh the files list
      this.filesResource.reload();
    });
  }

  deleteFile(): void {
    this.closeDeleteFileDialog();
    this.filesService.deleteFileFolApiV1FilesDeleteDelete({path: this.selectedFilePath, media_id: this.mediaId()}).subscribe((deleted) => {
      // Display the return message
      let msg: string = '';
      if (deleted) {
        msg = 'Deleted successfully!';
      } else {
        msg = 'Failed to delete!';
      }
      this.webSocketService.showToast(msg, deleted ? 'success' : 'error');
      // Refresh the files list
      this.filesResource.reload();
    });
  }

  @ViewChild('optionsDialog') optionsDialog!: ElementRef<HTMLDialogElement>;
  openOptionsDialog(): void {
    this.optionsDialog.nativeElement.showModal(); // Display the dialog
  }

  closeOptionsDialog(): void {
    this.optionsDialog.nativeElement.close(); // Close the dialog
  }

  @ViewChild('textDialog') textDialog!: ElementRef<HTMLDialogElement>;
  openTextDialog(): void {
    this.closeOptionsDialog();
    this.textFileLoading.set(true);
    this.selectedFileText.set([]);
    this.textDialog.nativeElement.showModal();
    this.filesService.readFileApiV1FilesReadGet({file_path: this.selectedFilePath}).subscribe({
      next: (content) => this.selectedFileText.set(content.split('\n')),
      complete: () => this.textFileLoading.set(false),
      error: () => this.textFileLoading.set(false),
    });
  }

  closeTextDialog(): void {
    this.textDialog.nativeElement.close(); // Close the dialog
  }

  @ViewChild('videoDialog') videoDialog!: ElementRef<HTMLDialogElement>;
  @ViewChild('videoDialogContent') videoDialogContent!: ElementRef<HTMLDivElement>;
  openVideoDialog(): void {
    // Display the dialog by passing the file path and title
    this.videoDialog.nativeElement.showModal();
    let videoUrl = `/api/v1/files/video?file_path=${encodeURIComponent(this.selectedFilePath)}`;
    // style="width: 75vw; height: auto; @media (width < 768px) { width: 100vw; }">
    let videoRef = `
      <style>
        video {
          width: 75vw;
          height: auto;
        }
        @media (max-width: 768px) {
          video {
            width: 100%;
          }
        }
      </style>
      <video controls controlsList="nodownload">
        <source src="${videoUrl}" type="video/mp4">
        Your browser does not support the video tag.</source>
      </video>`;
    this.videoDialogContent.nativeElement.innerHTML = videoRef;
  }

  closeVideoDialog(): void {
    this.videoDialogContent.nativeElement.innerHTML = ''; // Clear the video content
    this.videoDialog.nativeElement.close(); // Close the dialog
  }

  @ViewChild('videoInfoDialog') videoInfoDialog!: ElementRef<HTMLDialogElement>;
  openVideoInfoDialog(): void {
    // Display the dialog by passing the file path and title
    this.videoInfoLoading.set(true);
    this.videoInfoDialog.nativeElement.showModal();
    this.filesService.getVideoInfoApiV1FilesVideoInfoGet({file_path: this.selectedFilePath}).subscribe({
      next: (videoInfo) => {
        // let jsonString = JSON.stringify(videoInfo, null, 2);
        // this.videoInfo = jsonString.replace(/,/g, ',\n'); // Add new lines between keys
        // console.log('Audio Tracks: ', this.audioTracks);
        // console.log('Subtitle Tracks: ', this.subtitleTracks);
        this.videoInfo.set(videoInfo);
      },
      complete: () => this.videoInfoLoading.set(false),
      error: () => this.videoInfoLoading.set(false),
    });
  }

  closeVideoInfoDialog(): void {
    this.videoInfoDialog.nativeElement.close(); // Close the dialog
    this.videoInfo.set(null); // Clear the video info
  }

  @ViewChild('renameDialog') renameDialog!: ElementRef<HTMLDialogElement>;
  openRenameDialog(): void {
    this.closeOptionsDialog();
    // Display the rename dialog
    this.renameDialog.nativeElement.showModal();
  }

  closeRenameDialog(): void {
    this.renameDialog.nativeElement.close(); // Close the dialog
  }

  @ViewChild('deleteFileDialog') deleteFileDialog!: ElementRef<HTMLDialogElement>;
  openDeleteFileDialog(): void {
    this.closeOptionsDialog();
    // Display the delete confirmation dialog
    this.deleteFileDialog.nativeElement.showModal();
  }

  closeDeleteFileDialog(): void {
    this.deleteFileDialog.nativeElement.close(); // Close the dialog
  }
}

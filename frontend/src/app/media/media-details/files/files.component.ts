import {DatePipe, NgTemplateOutlet} from '@angular/common';
import {Component, computed, ElementRef, inject, input, resource, ViewChild} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {VideoInfo} from '../../../models/files';
import {FolderInfo} from '../../../models/media';
import {FilesService} from '../../../services/files.service';
import {MediaService} from '../../../services/media.service';
import {WebsocketService} from '../../../services/websocket.service';

interface ErrorMessage {
  error: {
    detail: string;
  };
}

@Component({
  selector: 'media-files',
  imports: [DatePipe, FormsModule, NgTemplateOutlet],
  templateUrl: './files.component.html',
  styleUrl: './files.component.scss',
})
export class FilesComponent {
  private readonly filesService = inject(FilesService);
  private readonly mediaService = inject(MediaService);
  private readonly webSocketService = inject(WebsocketService);

  mediaId = input.required<number>();
  filesLoading = true;
  textFileLoading = true;
  videoInfoLoading = true;
  // mediaFilesResponse: string = 'No files found';
  // mediaFiles: FolderInfo | undefined = undefined;

  selectedFilePath: string = '';
  selectedFileName: string = '';
  videoInfo: VideoInfo | undefined = undefined;
  selectedFileText: string[] = [];

  // Refresh the files list when the mediaId changes
  filesResource = resource({
    request: this.mediaId,
    loader: async ({request: mediaId}) => {
      this.filesLoading = true;
      return await this.mediaService.fetchMediaFiles(mediaId);
    },
  });

  filesError = computed(() => {
    const _error = this.filesResource.error() as ErrorMessage;
    // console.log('Files Error:', _error);
    return _error.error.detail;
  });

  // ngOnInit() {
  //   this.getMediaFiles();
  // }

  // getMediaFiles(): void {
  //   // Get Media Files
  //   this.mediaService.getMediaFiles(this.mediaId() + 1000).subscribe((files: FolderInfo | string) => {
  //     if (typeof files === 'string') {
  //       this.mediaFilesResponse = files;
  //     } else {
  //       this.mediaFiles = files;
  //     }
  //     this.filesLoading = false;
  //   });
  // }

  asFolderInfo(folder: FolderInfo): FolderInfo {
    // For use in ng-template for type checking
    return folder;
  }

  isTextFile(): boolean {
    const textFileExtensions = ['.txt', '.srt', '.log', '.json', '.py', '.sh'];
    return textFileExtensions.some((ext) => this.selectedFileName.endsWith(ext));
  }

  isVideoFile(): boolean {
    const videoFileExtensions = ['.mp4', '.mkv', '.avi', '.webm'];
    return videoFileExtensions.some((ext) => this.selectedFileName.endsWith(ext));
  }

  openFolderOrOptions(folder: FolderInfo): void {
    if (folder.type === 'folder') {
      folder.isExpanded = !folder.isExpanded;
    } else {
      this.selectedFilePath = folder.path;
      this.selectedFileName = folder.name;
      this.openOptionsDialog();
    }
  }

  renameFile(): void {
    this.closeRenameDialog();
    let selectedFileBasePath = this.selectedFilePath.split('/').slice(0, -1).join('/');
    let newName = selectedFileBasePath + '/' + this.selectedFileName;
    this.filesService.renameFileFolder(this.selectedFilePath, newName).subscribe((renamed) => {
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
    this.filesService.deleteFileFolder(this.selectedFilePath, this.mediaId()).subscribe((deleted) => {
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
    this.textFileLoading = true;
    this.selectedFileText = [];
    this.textDialog.nativeElement.showModal();
    this.filesService.getTextFile(this.selectedFilePath).subscribe((content) => {
      for (let line of content.split('\n')) {
        this.selectedFileText.push(line);
      }
      this.textFileLoading = false;
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
  audioTracks: string = '';
  subtitleTracks: string = '';
  openVideoInfoDialog(): void {
    // Display the dialog by passing the file path and title
    this.videoInfoLoading = true;
    this.audioTracks = '';
    this.subtitleTracks = '';
    this.videoInfoDialog.nativeElement.showModal();
    this.filesService.getVideoInfo(this.selectedFilePath).subscribe((videoInfo) => {
      // let jsonString = JSON.stringify(videoInfo, null, 2);
      // this.videoInfo = jsonString.replace(/,/g, ',\n'); // Add new lines between keys
      let audioTracksList: string[] = [];
      let subtitleTracksList: string[] = [];
      for (let stream of videoInfo.streams) {
        if (stream.codec_type.includes('audio')) {
          let _audioTrack = stream.language ? stream.language : 'unk';
          _audioTrack = _audioTrack + ' (' + stream.codec_name + ')';
          audioTracksList.push(_audioTrack);
        } else if (stream.codec_type.includes('subtitle')) {
          let _subtitleTrack = stream.language ? stream.language : 'unk';
          _subtitleTrack = _subtitleTrack + ' (' + stream.codec_name + ')';
          subtitleTracksList.push(_subtitleTrack);
        }
      }
      this.audioTracks = audioTracksList.join(', ');
      this.subtitleTracks = subtitleTracksList.join(', ');
      // console.log('Audio Tracks: ', this.audioTracks);
      // console.log('Subtitle Tracks: ', this.subtitleTracks);
      this.videoInfo = videoInfo;
      this.videoInfoLoading = false;
    });
  }

  closeVideoInfoDialog(): void {
    this.videoInfoDialog.nativeElement.close(); // Close the dialog
    this.videoInfo = undefined; // Clear the video info
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

import {AfterViewInit, ChangeDetectionStrategy, Component, ElementRef, input, output, viewChild} from '@angular/core';

@Component({
  selector: 'play-video-dialog',
  imports: [],
  templateUrl: './play-video-dialog.component.html',
  styleUrl: './play-video-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PlayVideoDialogComponent implements AfterViewInit {
  readonly filePath = input.required<string>();

  readonly closed = output<void>();

  readonly dialog = viewChild.required<ElementRef<HTMLDialogElement>>('videoDialog');
  readonly videoDialogContent = viewChild.required<ElementRef<HTMLDivElement>>('videoDialogContent');

  ngAfterViewInit(): void {
    this.openDialog();
  }

  private openDialog(): void {
    this.dialog().nativeElement.showModal();
    this.loadVideoContent();
  }

  private loadVideoContent(): void {
    const videoUrl = `/api/v1/files/video?file_path=${encodeURIComponent(this.filePath())}`;
    const videoRef = `
      <style>
        .video-body video {
          display: block;
          width: 100%;
          height: auto;
          max-height: calc(100vh - 12rem);
        }
      </style>
      <video controls controlsList="nodownload">
        <source src="${videoUrl}" type="video/mp4">
        Your browser does not support the video tag.</source>
      </video>`;
    this.videoDialogContent().nativeElement.innerHTML = videoRef;
  }

  closeDialog(): void {
    this.videoDialogContent().nativeElement.innerHTML = '';
    this.dialog().nativeElement.close();
    this.closed.emit();
  }
}

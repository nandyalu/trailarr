import {DatePipe, TitleCasePipe} from '@angular/common';
import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  computed,
  ElementRef,
  inject,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import {FilesService, VideoInfo} from 'generated-sources/openapi';
import {FileSizePipe} from 'src/app/helpers/file-size.pipe';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';

@Component({
  selector: 'video-info-dialog',
  imports: [DatePipe, TitleCasePipe, FileSizePipe, LoadIndicatorComponent],
  templateUrl: './video-info-dialog.component.html',
  styleUrl: './video-info-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VideoInfoDialogComponent implements AfterViewInit {
  private readonly filesService = inject(FilesService);

  readonly filePath = input.required<string>();

  readonly closed = output<void>();

  readonly dialog = viewChild.required<ElementRef<HTMLDialogElement>>('videoInfoDialog');

  protected readonly videoInfoLoading = signal(true);
  protected readonly videoInfo = signal<VideoInfo | null>(null);

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

  ngAfterViewInit(): void {
    this.openDialog();
  }

  private openDialog(): void {
    this.videoInfoLoading.set(true);
    this.dialog().nativeElement.showModal();
    this.loadVideoInfo();
  }

  private loadVideoInfo(): void {
    this.filesService.getVideoInfoApiV1FilesVideoInfoGet({file_path: this.filePath()}).subscribe({
      next: (videoInfo) => {
        // Handle case where youtube_channel is 'UnknownChannel'
        if (videoInfo && videoInfo.youtube_channel) {
          if (videoInfo.youtube_channel.toLowerCase() === 'unknownchannel') {
            videoInfo.youtube_channel = undefined;
          }
        }
        return this.videoInfo.set(videoInfo);
      },
      complete: () => this.videoInfoLoading.set(false),
      error: () => this.videoInfoLoading.set(false),
    });
  }

  closeDialog(): void {
    this.dialog().nativeElement.close();
    this.videoInfo.set(null);
    this.closed.emit();
  }
}

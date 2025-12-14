import {AfterViewInit, Component, ElementRef, inject, input, output, signal, viewChild} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {FilesService} from 'generated-sources/openapi';
import {WebsocketService} from '../../../../../services/websocket.service';
import {LoadIndicatorComponent} from '../../../../../shared/load-indicator';

@Component({
  selector: 'video-edit-dialog',
  imports: [FormsModule, LoadIndicatorComponent],
  templateUrl: './video-edit-dialog.component.html',
  styleUrl: './video-edit-dialog.component.scss',
})
export class VideoEditDialogComponent implements AfterViewInit {
  private readonly filesService = inject(FilesService);
  private readonly webSocketService = inject(WebsocketService);

  filePath = input.required<string>();
  fileName = input.required<string>();
  closed = output<void>();
  videoTrimmed = output<void>();

  protected readonly startTimestamp = signal<string>('0');
  protected readonly endTimestamp = signal<string>('');
  protected readonly outputFileName = signal<string>('');
  protected readonly isProcessing = signal<boolean>(false);

  // Getter and setter methods for ngModel binding
  get startTime(): string {
    return this.startTimestamp();
  }
  set startTime(value: string) {
    this.startTimestamp.set(value);
  }

  get endTime(): string {
    return this.endTimestamp();
  }
  set endTime(value: string) {
    this.endTimestamp.set(value);
  }

  get outputFile(): string {
    return this.outputFileName();
  }
  set outputFile(value: string) {
    this.outputFileName.set(value);
  }

  readonly videoEditDialog = viewChild.required<ElementRef<HTMLDialogElement>>('videoEditDialog');
  readonly videoElement = viewChild<ElementRef<HTMLVideoElement>>('videoElement');

  ngAfterViewInit() {
    this.openDialog();
    // Set default output filename with '_trimmed' prefix
    const fileName = this.fileName();
    const dotIndex = fileName.lastIndexOf('.');
    if (dotIndex > 0) {
      const nameWithoutExt = fileName.substring(0, dotIndex);
      const extension = fileName.substring(dotIndex);
      this.outputFileName.set(`${nameWithoutExt}_trimmed${extension}`);
    } else {
      this.outputFileName.set(`${fileName}_trimmed`);
    }
    // Load video duration when dialog opens
    const video = this.videoElement()?.nativeElement;
    if (video) {
      video.addEventListener('loadedmetadata', () => {
        if (video.duration && !this.endTimestamp()) {
          this.endTimestamp.set(this.formatTime(video.duration));
        }
      });
    }
  }

  private openDialog(): void {
    this.videoEditDialog().nativeElement.showModal();
  }

  private closeDialog(): void {
    this.videoEditDialog().nativeElement.close();
  }

  protected setCurrentTimeAsStart() {
    const video = this.videoElement()?.nativeElement;
    if (video) {
      this.startTimestamp.set(this.formatTime(video.currentTime));
    }
  }

  protected setCurrentTimeAsEnd() {
    const video = this.videoElement()?.nativeElement;
    if (video) {
      this.endTimestamp.set(this.formatTime(video.currentTime));
    }
  }

  protected seekToStart() {
    const video = this.videoElement()?.nativeElement;
    if (video && this.startTimestamp()) {
      video.currentTime = this.parseTime(this.startTimestamp());
    }
  }

  protected seekToEnd() {
    const video = this.videoElement()?.nativeElement;
    if (video && this.endTimestamp()) {
      video.currentTime = this.parseTime(this.endTimestamp());
    }
  }

  private formatTime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
      return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
  }

  private parseTime(timeStr: string): number {
    const parts = timeStr.split(':').map((part) => parseInt(part, 10));
    if (parts.length === 3) {
      // HH:MM:SS
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    } else if (parts.length === 2) {
      // MM:SS
      return parts[0] * 60 + parts[1];
    } else if (parts.length === 1) {
      // SS
      return parts[0];
    }
    return 0;
  }

  protected trimVideo() {
    if (!this.validateInputs()) {
      return;
    }

    this.isProcessing.set(true);

    // Get the folder path from the full file path
    const folderPath = this.filePath().substring(0, this.filePath().lastIndexOf('/'));
    const outputPath = `${folderPath}/${this.outputFileName()}`;

    const startTime = this.parseTime(this.startTimestamp());
    const endTime = this.parseTime(this.endTimestamp());

    this.filesService
      .trimVideoApiV1FilesTrimVideoPost({
        file_path: this.filePath(),
        output_file: outputPath,
        start_timestamp: startTime,
        end_timestamp: endTime,
      })
      .subscribe({
        next: (result) => {
          this.webSocketService.showToast(result, 'success');
          this.videoTrimmed.emit();
          this.closeVideoEditDialog();
        },
        error: (error) => {
          console.error('Error trimming video:', error);
          this.webSocketService.showToast('Failed to trim video', 'error');
          this.isProcessing.set(false);
        },
        complete: () => {
          this.isProcessing.set(false);
        },
      });
  }

  private validateInputs(): boolean {
    const startTime = this.parseTime(this.startTimestamp());
    const endTime = this.parseTime(this.endTimestamp());

    if (startTime >= endTime) {
      this.webSocketService.showToast('Start time must be less than end time', 'error');
      return false;
    }

    if (!this.outputFileName().trim()) {
      this.webSocketService.showToast('Output filename is required', 'error');
      return false;
    }

    return true;
  }

  protected closeVideoEditDialog(): void {
    this.closeDialog();
    this.closed.emit();
  }

  protected getVideoUrl(): string {
    return `/api/v1/files/video?file_path=${encodeURIComponent(this.filePath())}`;
  }
}

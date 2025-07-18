import { Component, input, signal } from '@angular/core';
import { MediaService } from '../../../services/media.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LoadIndicatorComponent } from 'src/app/shared/load-indicator';
import { TooltipModule } from 'primeng/tooltip';
import { Media } from 'src/app/models/media';

@Component({
  selector: 'app-media-downloads',
  templateUrl: './media-downloads.component.html',
  styleUrls: ['./media-downloads.component.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule, LoadIndicatorComponent, TooltipModule],
})
export class MediaDownloadsComponent {
  mediaId = input.required<number>();
  media = signal<Media | null>(null);

  constructor(private mediaService: MediaService) {
    this.mediaService.selectedMedia.subscribe((media) => {
      if (media && media.id === this.mediaId()) {
        this.media.set(media);
      }
    });
  }

  refresh() {
    this.mediaService.scanMedia(this.mediaId()).subscribe();
  }

  formatDuration(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  formatSize(bytes: number): string {
    if (bytes === 0) {
      return '0 Bytes';
    }
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}

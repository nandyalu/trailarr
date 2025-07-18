import { Component, computed, inject, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MediaService } from 'src/app/services/media.service';
import { WebsocketService } from 'src/app/services/websocket.service';
import {bytesToSize, durationToTime} from 'src/app/helpers/converters';
import { LoadIndicatorComponent } from 'src/app/shared/load-indicator';

@Component({
  selector: 'app-media-downloads',
  standalone: true,
  imports: [CommonModule, LoadIndicatorComponent],
  templateUrl: './media-downloads.component.html',
  styleUrls: ['./media-downloads.component.scss'],
})
export class MediaDownloadsComponent {
  private readonly mediaService = inject(MediaService);
  private readonly webSocketService = inject(WebsocketService);

  mediaId = input.required<number>();
  selectedMedia = this.mediaService.selectedMedia;
  isLoading = computed(() => this.mediaService.mediaResource.isLoading());

  bytesToSize = bytesToSize;
  durationToTime = durationToTime;

  refreshDownloads() {
    this.webSocketService.showToast('Refreshing downloads...');
    this.mediaService.scanMediaDownloads(this.mediaId()).subscribe((res: string) => {
      console.log(res);
      this.webSocketService.showToast(res, 'success');
    });
  }

  getTooltip(download: any): string {
    return `
      Path: ${download.path}
      File Name: ${download.file_name}
      Size: ${this.bytesToSize(download.size)}
      Updated At: ${download.updated_at}
      Resolution: ${download.resolution}
      Video Format: ${download.video_format}
      Audio Format: ${download.audio_format}
      Audio Channels: ${download.audio_channels}
      File Format: ${download.file_format}
      Duration: ${this.durationToTime(download.duration)}
      Subtitles: ${download.subtitles}
      Added At: ${download.added_at}
      Profile ID: ${download.profile_id}
      File Exists: ${download.file_exists}
    `;
  }
}

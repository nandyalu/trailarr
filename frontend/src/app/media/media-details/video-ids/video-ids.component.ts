import {ChangeDetectionStrategy, Component, inject, input, signal, viewChild, ElementRef} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {firstValueFrom} from 'rxjs';
import {VideoId, VideoIdCreate, VIDEO_TYPE_OPTIONS, SOURCE_LABELS, VideoIdSource} from '../../../models/videoid';
import {MediaService} from '../../../services/media.service';
import {httpResource} from '@angular/common/http';

@Component({
  selector: 'app-video-ids',
  templateUrl: './video-ids.component.html',
  styleUrl: './video-ids.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule],
})
export class VideoIdsComponent {
  private readonly mediaService = inject(MediaService);

  readonly mediaId = input.required<number>();

  readonly videoTypeOptions = VIDEO_TYPE_OPTIONS;
  readonly sourceLabels = SOURCE_LABELS;

  readonly dialogRef = viewChild<ElementRef<HTMLDialogElement>>('addDialog');

  // Form state
  newVideoType = signal<string>('trailer');
  newLanguage = signal<string>('');
  newYoutubeId = signal<string>('');
  isSaving = signal<boolean>(false);
  formError = signal<string>('');

  readonly videoIdsResource = httpResource<VideoId[]>(
    () => ({url: `/api/v1/media/${this.mediaId()}/video-ids`}),
    {defaultValue: []},
  );

  sourceLabel(source: VideoIdSource): string {
    return this.sourceLabels[source] ?? source;
  }

  youtubeUrl(youtubeId: string): string {
    return `https://www.youtube.com/watch?v=${youtubeId}`;
  }

  openDialog(): void {
    this.newVideoType.set('trailer');
    this.newLanguage.set('');
    this.newYoutubeId.set('');
    this.formError.set('');
    this.dialogRef()?.nativeElement.showModal();
  }

  closeDialog(): void {
    this.dialogRef()?.nativeElement.close();
  }

  async addVideoId(): Promise<void> {
    const youtubeId = this.newYoutubeId().trim();
    if (!youtubeId) {
      this.formError.set('YouTube ID is required.');
      return;
    }
    const cleanId = extractYoutubeId(youtubeId);
    if (!cleanId) {
      this.formError.set('Invalid YouTube ID or URL.');
      return;
    }
    const payload: VideoIdCreate = {
      video_type: this.newVideoType(),
      language: this.newLanguage().trim().slice(0, 2).toLowerCase(),
      youtube_id: cleanId,
    };
    this.isSaving.set(true);
    this.formError.set('');
    try {
      await firstValueFrom(this.mediaService.createVideoId(this.mediaId(), payload));
      this.videoIdsResource.reload();
      this.closeDialog();
    } catch {
      this.formError.set('Failed to save. Please try again.');
    } finally {
      this.isSaving.set(false);
    }
  }

  async deleteVideoId(id: number): Promise<void> {
    await firstValueFrom(this.mediaService.deleteVideoId(this.mediaId(), id));
    this.videoIdsResource.reload();
  }
}

function extractYoutubeId(input: string): string | null {
  const trimmed = input.trim();
  // Already an ID (11 chars, no slash/dot)
  if (/^[A-Za-z0-9_-]{11}$/.test(trimmed)) return trimmed;
  // Full URL
  try {
    const url = new URL(trimmed);
    const v = url.searchParams.get('v');
    if (v) return v;
    // youtu.be/ID
    const parts = url.pathname.split('/').filter(Boolean);
    if (parts.length > 0 && /^[A-Za-z0-9_-]{11}$/.test(parts[parts.length - 1])) {
      return parts[parts.length - 1];
    }
  } catch {
    // not a URL
  }
  return null;
}

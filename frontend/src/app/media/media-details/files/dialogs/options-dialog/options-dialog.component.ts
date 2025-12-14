import {AfterViewInit, ChangeDetectionStrategy, Component, computed, ElementRef, input, output, signal, viewChild} from '@angular/core';
import {VideoEditDialogComponent} from 'src/app/media/media-details/files/dialogs/video-edit-dialog/video-edit-dialog.component';
import {DeleteDialogComponent} from '../delete-dialog/delete-dialog.component';
import {PlayVideoDialogComponent} from '../play-video-dialog/play-video-dialog.component';
import {RenameDialogComponent} from '../rename-dialog/rename-dialog.component';
import {TextDialogComponent} from '../text-dialog/text-dialog.component';
import {VideoInfoDialogComponent} from '../video-info-dialog/video-info-dialog.component';

export type DialogOptions = 'text' | 'video' | 'videoInfo' | 'rename' | 'delete' | 'videoEdit';

@Component({
  selector: 'app-options-dialog',
  standalone: true,
  imports: [
    TextDialogComponent,
    PlayVideoDialogComponent,
    VideoInfoDialogComponent,
    RenameDialogComponent,
    DeleteDialogComponent,
    VideoEditDialogComponent,
  ],
  templateUrl: './options-dialog.component.html',
  styleUrl: './options-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OptionsDialogComponent implements AfterViewInit {
  readonly filePath = input.required<string>();
  readonly fileName = input.required<string>();
  readonly mediaId = input.required<number>();

  readonly closed = output<void>();
  readonly filesRefreshed = output<void>();

  readonly dialog = viewChild.required<ElementRef<HTMLDialogElement>>('optionsDialog');

  protected readonly openDialogType = signal<DialogOptions | null>(null);

  protected readonly isVideoFile = computed(() => ['.mp4', '.mkv', '.avi', '.webm'].some((ext) => this.fileName().endsWith(ext)));
  protected readonly isTextFile = computed(() =>
    ['.txt', '.srt', '.log', '.json', '.py', '.sh'].some((ext) => this.fileName().endsWith(ext)),
  );

  ngAfterViewInit(): void {
    this.openOptionsDialog();
  }

  private openOptionsDialog(): void {
    this.dialog().nativeElement.showModal();
  }

  closeDialog(emit: boolean): void {
    this.dialog().nativeElement.close();
    if (emit) {
      setTimeout(() => {
        this.closed.emit();
      }, 500);
    }
  }

  protected openDialog(type: DialogOptions): void {
    this.closeDialog(false);
    this.openDialogType.set(type);
  }

  protected closeChildDialog(): void {
    setTimeout(() => {
      this.openDialogType.set(null);
      this.closed.emit();
    }, 500);
  }

  onRenameComplete(): void {
    this.openDialogType.set(null);
    this.filesRefreshed.emit();
  }

  onDeleteComplete(): void {
    this.openDialogType.set(null);
    this.filesRefreshed.emit();
  }

  onVideoTrimComplete(): void {
    this.openDialogType.set(null);
    this.filesRefreshed.emit();
  }
}

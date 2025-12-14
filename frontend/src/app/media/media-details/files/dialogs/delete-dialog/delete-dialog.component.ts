import {AfterViewInit, ChangeDetectionStrategy, Component, ElementRef, inject, input, output, viewChild} from '@angular/core';
import {FilesService} from 'generated-sources/openapi';
import {WebsocketService} from 'src/app/services/websocket.service';

@Component({
  selector: 'delete-dialog',
  imports: [],
  templateUrl: './delete-dialog.component.html',
  styleUrl: './delete-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DeleteDialogComponent implements AfterViewInit {
  private readonly filesService = inject(FilesService);
  private readonly webSocketService = inject(WebsocketService);

  readonly filePath = input.required<string>();
  readonly fileName = input.required<string>();
  readonly mediaId = input.required<number>();

  readonly closed = output<void>();
  readonly deleted = output<void>();

  readonly dialog = viewChild.required<ElementRef<HTMLDialogElement>>('deleteDialog');

  ngAfterViewInit(): void {
    this.openDialog();
  }

  private openDialog(): void {
    this.dialog().nativeElement.showModal();
  }

  deleteFile(): void {
    this.filesService.deleteFileFolApiV1FilesDeleteDelete({path: this.filePath(), media_id: this.mediaId()}).subscribe((result) => {
      const msg = result ? 'Deleted successfully!' : 'Failed to delete!';
      this.webSocketService.showToast(msg, result ? 'success' : 'error');
      this.closeDialog();
      this.deleted.emit();
    });
  }

  closeDialog(): void {
    this.dialog().nativeElement.close();
    this.closed.emit();
  }
}

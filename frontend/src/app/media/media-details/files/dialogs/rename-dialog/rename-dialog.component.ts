import {AfterViewInit, ChangeDetectionStrategy, Component, ElementRef, inject, input, output, signal, viewChild} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {FilesService} from 'generated-sources/openapi';
import {WebsocketService} from 'src/app/services/websocket.service';

@Component({
  selector: 'rename-dialog',
  imports: [FormsModule],
  templateUrl: './rename-dialog.component.html',
  styleUrl: './rename-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RenameDialogComponent implements AfterViewInit {
  private readonly filesService = inject(FilesService);
  private readonly webSocketService = inject(WebsocketService);

  readonly filePath = input.required<string>();
  readonly fileName = input.required<string>();

  readonly closed = output<void>();
  readonly renamed = output<void>();

  readonly dialog = viewChild.required<ElementRef<HTMLDialogElement>>('renameDialog');

  protected readonly renamedFileName = signal('');

  ngAfterViewInit(): void {
    this.openDialog();
  }

  private openDialog(): void {
    this.renamedFileName.set(this.fileName());
    this.dialog().nativeElement.showModal();
  }

  renameFile(): void {
    let selectedFileBasePath = this.filePath().split('/').slice(0, -1).join('/');
    let newPath = selectedFileBasePath + '/' + this.renamedFileName();
    this.filesService.renameFileFolApiV1FilesRenamePost({old_path: this.filePath(), new_path: newPath}).subscribe((result) => {
      const msg = result ? 'File renamed successfully!' : 'Failed to rename file!';
      this.webSocketService.showToast(msg, result ? 'success' : 'error');
      this.closeDialog();
      this.renamed.emit();
    });
  }

  closeDialog(): void {
    this.dialog().nativeElement.close();
    this.closed.emit();
  }
}

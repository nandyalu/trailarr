import {AfterViewInit, ChangeDetectionStrategy, Component, ElementRef, inject, input, output, signal, viewChild} from '@angular/core';
import {FilesService} from 'generated-sources/openapi';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {jsonEqual} from 'src/util';

@Component({
  selector: 'text-dialog',
  imports: [LoadIndicatorComponent],
  templateUrl: './text-dialog.component.html',
  styleUrl: './text-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TextDialogComponent implements AfterViewInit {
  private readonly filesService = inject(FilesService);

  readonly filePath = input.required<string>();
  readonly fileName = input.required<string>();

  readonly closed = output<void>();

  readonly dialog = viewChild.required<ElementRef<HTMLDialogElement>>('dialog');

  protected readonly textFileLoading = signal(true);
  protected readonly selectedFileText = signal<string[]>([], {equal: jsonEqual});

  ngAfterViewInit(): void {
    this.openDialog();
  }

  private openDialog(): void {
    this.dialog().nativeElement.showModal();
    this.textFileLoading.set(true);
    this.selectedFileText.set([]);
    this.loadFileContent();
  }

  private loadFileContent(): void {
    this.filesService.readFileApiV1FilesReadGet({file_path: this.filePath()}).subscribe({
      next: (content) => this.selectedFileText.set(content.split('\n')),
      complete: () => this.textFileLoading.set(false),
      error: () => this.textFileLoading.set(false),
    });
  }

  closeDialog(): void {
    this.dialog().nativeElement.close();
    this.closed.emit();
  }
}

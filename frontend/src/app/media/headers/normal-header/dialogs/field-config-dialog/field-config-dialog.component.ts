import {AfterViewInit, ChangeDetectionStrategy, Component, ElementRef, input, output, signal, viewChild} from '@angular/core';

export interface FieldOption {
  key: string;
  label: string;
}

@Component({
  selector: 'app-field-config-dialog',
  imports: [],
  templateUrl: './field-config-dialog.component.html',
  styleUrl: './field-config-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FieldConfigDialogComponent implements AfterViewInit {
  readonly fieldOptions = input.required<FieldOption[]>();
  readonly selectedFields = input.required<string[]>();

  readonly fieldsChanged = output<string[]>();
  readonly closed = output<void>();

  protected readonly localSelected = signal<string[]>([]);
  private readonly dialog = viewChild.required<ElementRef<HTMLDialogElement>>('fieldConfigDialog');

  ngAfterViewInit(): void {
    this.localSelected.set([...this.selectedFields()]);
    this.dialog().nativeElement.showModal();
  }

  protected isChecked(key: string): boolean {
    return this.localSelected().includes(key);
  }

  protected toggleField(key: string, checked: boolean): void {
    if (checked) {
      this.localSelected.update((f) => [...f, key]);
    } else {
      this.localSelected.update((f) => f.filter((k) => k !== key));
    }
  }

  protected onConfirm(): void {
    this.fieldsChanged.emit([...this.localSelected()]);
    this.closeDialog();
  }

  protected onCancel(): void {
    this.closeDialog();
  }

  private closeDialog(): void {
    this.dialog().nativeElement.close();
    setTimeout(() => this.closed.emit(), 150);
  }
}

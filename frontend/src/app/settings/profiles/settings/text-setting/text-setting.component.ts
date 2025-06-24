import {ChangeDetectionStrategy, Component, inject, input, model, OnChanges, output, signal, ViewContainerRef} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {PathSelectDialogComponent} from 'src/app/shared/path-select-dialog/path-select-dialog.component';

@Component({
  selector: 'app-text-setting',
  imports: [FormsModule],
  templateUrl: './text-setting.component.html',
  styleUrl: './text-setting.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TextSettingComponent implements OnChanges {
  // Setting a unique ID for the input element, setting a signal value gives a browser warning
  // so we generate a random string for the ID
  readonly inputId = 'text-setting-' + Math.random().toString(36).substring(2, 10);

  private viewContainerRef = inject(ViewContainerRef);

  // Define the inputs for the component
  name = input.required<string>();
  description = input<string>('');
  descriptionExtra = input<string>('');
  isNumberType = input.required<boolean>();
  isLongInput = input.required<boolean>();
  showFolderButton = input<boolean>(false);
  pathShouldEndWith = input<string>('');
  placeholder = input<string>('');
  value = model.required<string | number>();
  minLength = input<number>(0);
  maxLength = input<number>(150);
  autocomplete = input<string>('off');
  disabled = input<boolean>(false);

  oldValue = signal<string | number>('');
  onSubmit = output<string>();

  // ngOnInit() {
  //   this.oldValue.set(this.value());
  // }

  ngOnChanges() {
    this.oldValue.set(this.value());
  }

  openPathSelectDialog(): void {
    // Open the dialog for selecting a path value
    const dialogRef = this.viewContainerRef.createComponent(PathSelectDialogComponent);
    dialogRef.setInput('name', this.name());
    dialogRef.setInput('path', this.value());
    dialogRef.setInput('pathShouldEndWith', this.pathShouldEndWith());
    dialogRef.instance.onSubmit.subscribe((emitValue: string) => {
      if (emitValue) {
        // Submit the value back to caller
        this.value.set(emitValue);
        this.onSubmitValue();
      }
      // Else, dialog closed without submission, do nothing
      setTimeout(() => {
        dialogRef.destroy(); // Destroy the dialog component after use
      }, 2000);
    });
  }

  resetValue(): void {
    this.value.set(this.oldValue());
  }

  onSubmitValue(): void {
    let submitValue = this.value();
    submitValue = submitValue.toString().trim();
    this.onSubmit.emit(submitValue);
    this.oldValue.set(submitValue);
  }
}

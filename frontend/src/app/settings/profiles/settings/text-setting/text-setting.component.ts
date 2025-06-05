import {Component, input, model, OnChanges, output, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';

@Component({
  selector: 'app-text-setting',
  imports: [FormsModule],
  templateUrl: './text-setting.component.html',
  styleUrl: './text-setting.component.scss',
})
export class TextSettingComponent implements OnChanges {
  // Setting a unique ID for the input element, setting a signal value gives a browser warning
  // so we generate a random string for the ID
  readonly inputId = 'text-setting-' + Math.random().toString(36).substring(2, 10);

  // Define the inputs for the component
  name = input.required<string>();
  description = input<string>('');
  descriptionExtra = input<string>('');
  isNumberType = input.required<boolean>();
  isLongInput = input.required<boolean>();
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

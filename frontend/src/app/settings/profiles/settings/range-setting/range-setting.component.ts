import {ChangeDetectionStrategy, Component, input, model, output, signal} from '@angular/core';
import {FormsModule} from '@angular/forms';

@Component({
  selector: 'app-range-setting',
  imports: [FormsModule],
  templateUrl: './range-setting.component.html',
  styleUrl: './range-setting.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RangeSettingComponent {
  // Setting a unique ID for the input element, setting a signal value gives a browser warning
  // so we generate a random string for the ID
  readonly inputId = 'range-setting-' + Math.random().toString(36).substring(2, 10);

  // Define the inputs for the component
  name = input.required<string>();
  description = input<string>('');
  descriptionExtra = input<string>('');
  value = model.required<string | number>();
  minValue = input<number>(0);
  maxValue = input<number>(150);
  stepValue = input<number>(5);
  disabled = input<boolean>(false);
  colorType = input<'default' | 'warning' | 'danger'>('default');

  oldValue = signal<string | number>('');
  onSubmit = output<string>();

  ngOnInit() {
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

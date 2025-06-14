import {ChangeDetectionStrategy, Component, input, output} from '@angular/core';

@Component({
  selector: 'app-options-setting',
  imports: [],
  templateUrl: './options-setting.component.html',
  styleUrl: './options-setting.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OptionsSettingComponent {
  // Setting a unique ID for the input element, setting a signal value gives a browser warning
  // so we generate a random string for the ID
  readonly inputId = 'options-setting-' + Math.random().toString(36).substring(2, 10);

  name = input.required<string>();
  description = input<string>('');
  descriptionExtra = input<string>('');
  options = input.required<string[]>();
  selectedOption = input('', {transform: String});
  optionChange = output<string>();

  onOptionClick(option: string): void {
    this.optionChange.emit(option);
  }
}

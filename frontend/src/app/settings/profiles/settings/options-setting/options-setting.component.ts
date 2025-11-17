import {CommonModule} from '@angular/common';
import {ChangeDetectionStrategy, Component, input, output} from '@angular/core';
@Component({
  selector: 'app-options-setting',
  imports: [CommonModule],
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
  disabledOptions = input<string[]>([]);
  selectedOption = input('', {transform: String});
  colorType = input<'default' | 'warning' | 'danger'>('default');
  colorTypeOption = input<string>('');

  optionChange = output<string>();

  getOptionClasses(option: string): string[] {
    const option_ = option.toLowerCase();
    const colorTypeOption_ = this.colorTypeOption().toLowerCase();
    const selectedOption_ = this.selectedOption().toLowerCase();
    const classes = ['option-label'];

    // Check if the option is the selected option
    if (option_ === selectedOption_) {
      classes.push('option__selected');
    }
    // Check if the option is disabled
    if (this.disabledOptions().includes(option)) {
      classes.push('option__disabled');
    }
    // Check if the option matches the color type option
    if (this.colorTypeOption() !== '' && option_ === colorTypeOption_) {
      const highlighterClass = 'option__' + this.colorType().toLowerCase();
      classes.push(highlighterClass);
    }

    return classes;
  }

  onOptionClick(option: string): void {
    this.optionChange.emit(option);
  }
}

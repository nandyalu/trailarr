import {ChangeDetectionStrategy, Component, HostBinding} from '@angular/core';

@Component({
  selector: 'app-load-indicator',
  template: `<div class="loading-bar"></div>
    <div class="loading-bar"></div>
    <div class="loading-bar"></div>
    <div class="loading-bar"></div>`,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [],
})
export class LoadIndicatorComponent {
  @HostBinding('class') hostClass = 'loading-wave';
}

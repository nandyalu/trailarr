import {TitleCasePipe} from '@angular/common';
import {ChangeDetectionStrategy, Component, computed, inject} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Settings} from 'generated-sources/openapi';
import {WebsocketService} from 'src/app/services/websocket.service';
import {HelpLinkIconComponent} from 'src/app/shared/help-link-icon/help-link-icon.component';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {SettingsService} from '../../services/settings.service';
import {OptionsSettingComponent} from '../profiles/settings/options-setting/options-setting.component';
import {TextSettingComponent} from '../profiles/settings/text-setting/text-setting.component';

@Component({
  selector: 'app-trailer',
  imports: [FormsModule, HelpLinkIconComponent, LoadIndicatorComponent, OptionsSettingComponent, TextSettingComponent, TitleCasePipe],
  templateUrl: './general.component.html',
  styleUrl: './general.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GeneralComponent {
  private readonly settingsService = inject(SettingsService);
  private webSocketService = inject(WebsocketService);

  protected readonly isLoading = this.settingsService.settingsResource.isLoading;
  protected readonly settings = this.settingsService.settingsResource.value;

  loggingOptions = ['Debug', 'Info', 'Warning', 'Error'];
  trueFalseOptions = ['true', 'false'];
  themeOptions = ['Auto', 'Dark', 'Light'];
  helpLinks = {
    general: 'https://nandyalu.github.io/trailarr/user-guide/settings/general-settings/',
    files: 'https://nandyalu.github.io/trailarr/user-guide/settings/general-settings/#file-settings',
    advanced: 'https://nandyalu.github.io/trailarr/user-guide/settings/general-settings/#advanced-settings',
    experimental: 'https://nandyalu.github.io/trailarr/user-guide/settings/general-settings/#experimental-settings',
  };

  warningMessages = computed(() => {
    const messages: string[] = [];
    if (this.settings()?.log_level === 'DEBUG') {
      messages.push("Log Level set to 'Debug', this will generate too many logs in the console, change it if not needed!");
    }
    if (this.settings()?.monitor_enabled === false) {
      messages.push('Monitor is disabled, trailers will not be downloaded automatically.');
    }
    return messages;
  });

  toTitleCase(str: string): string {
    return str
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  }

  updateSetting(key: keyof Settings, value: any) {
    this.settingsService.updateSetting(key, value).subscribe((msg) => {
      // Show update result message
      const status = msg.toLowerCase().includes('error') ? 'Error' : 'Success';
      this.webSocketService.showToast(msg, status);
      // Update the settings after the change
      this.settingsService.settingsResource.reload();
    });
  }
}

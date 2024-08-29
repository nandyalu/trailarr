import { NgFor, NgIf } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Settings } from '../../models/settings';
import { SettingsService } from '../../services/settings.service';

@Component({
  selector: 'app-trailer',
  standalone: true,
  imports: [NgIf, NgFor, FormsModule],
  templateUrl: './trailer.component.html',
  styleUrl: './trailer.component.css'
})
export class TrailerComponent {
  settings?: Settings;
  updateResults: String[] = [];
  monitorInterval = 60;
  resolution = 1080;
  subtitleLanguage = 'en';
  trueFalseOptions = [true, false];
  fileFormats = ["mkv", "mp4", "webm"];
  audioFormats = ["aac", "ac3", "eac3", "flac", "opus"]
  videoFormats = ["h264", "h265", "vp8", "vp9", "av1"]
  subtitleFormats = ["srt", "vtt", "pgs"]
  ytCookiesPath = "";

  constructor(private settingsService: SettingsService) { }

  ngOnInit() {
    this.getSettings();
  }

  getSettings() {
    this.settingsService.getSettings().subscribe(settings => {
      this.settings = settings;
      this.monitorInterval = settings.monitor_interval;
      this.resolution = settings.trailer_resolution;
      this.subtitleLanguage = settings.trailer_subtitles_language;
    });
  }

  updateSetting(key: keyof Settings, value: any) {
    // Do not update if setting value hasn't changed
    if (this.settings? this.settings[key] === value : false) {
      return;
    }
    this.settingsService.updateSetting(key, value).subscribe(msg => {
      // Add update result message to end of list
      this.updateResults.push(msg);
      // Update the settings after the change
      this.getSettings();
      // Hide the message after 3 seconds
      setTimeout(() => {
        // Remove the first message (oldest) from the list
        this.updateResults.shift();
      }, 3000);
    });
  }
}

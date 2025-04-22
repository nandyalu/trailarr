import {NgFor, NgIf} from '@angular/common';
import {Component} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Settings} from '../../models/settings';
import {SettingsService} from '../../services/settings.service';

@Component({
  selector: 'app-trailer',
  imports: [NgIf, NgFor, FormsModule],
  templateUrl: './trailer.component.html',
  styleUrl: './trailer.component.scss',
})
export class TrailerComponent {
  isLoading: boolean = false;
  settings?: Settings;
  updateResults: String[] = [];
  monitorInterval = 60;
  resolution = 1080;
  audioVolumeLevel = 100;
  subtitleLanguage = 'en';
  loggingOptions = ['Debug', 'Info', 'Warning', 'Error'];
  trueFalseOptions = [true, false];
  fileFormats = ['mkv', 'mp4', 'webm'];
  audioFormats = ['aac', 'ac3', 'eac3', 'flac', 'opus'];
  videoFormats = ['h264', 'h265', 'vp8', 'vp9', 'av1'];
  subtitleFormats = ['srt', 'vtt'];
  trailerFileName = '';
  ytCookiesPath = '';
  excludeWords = '';
  minDuration = 30;
  maxDuration = 600;
  trailerSearchQuery = '';
  urlBase = '';

  constructor(private settingsService: SettingsService) {}

  ngOnInit() {
    this.isLoading = true;
    this.getSettings();
  }

  getSettings() {
    this.settingsService.getSettings().subscribe((settings) => {
      this.settings = settings;
      this.monitorInterval = settings.monitor_interval;
      this.resolution = settings.trailer_resolution;
      this.subtitleLanguage = settings.trailer_subtitles_language;
      this.trailerFileName = settings.trailer_file_name;
      this.ytCookiesPath = settings.yt_cookies_path;
      this.excludeWords = settings.exclude_words;
      this.minDuration = settings.trailer_min_duration;
      this.maxDuration = settings.trailer_max_duration;
      this.trailerSearchQuery = settings.trailer_search_query;
      this.urlBase = settings.url_base;
      this.isLoading = false;
    });
  }

  updateSetting(key: keyof Settings, value: any) {
    // Do not update if setting value hasn't changed
    if (this.settings ? this.settings[key] === value : false) {
      return;
    }
    // Special handling for trailer_file_format
    if (key === 'trailer_file_format') {
      // If the file format is webm, ensure the audio and video formats are compatible
      let videoCodec = this.settings?.trailer_video_format;
      if (value.toLowerCase() === 'webm') {
        if (this.settings?.trailer_audio_format != 'opus') {
          this.updateSetting('trailer_audio_format', 'opus');
        }
        if (videoCodec != 'vp8' && videoCodec != 'vp9' && videoCodec != 'av1') {
          this.updateSetting('trailer_video_format', 'vp9');
        }
      }
      // If the file format is mp4, ensure the audio and video formats are compatible
      if (value.toLowerCase() === 'mp4') {
        if (videoCodec != 'h264' && videoCodec != 'h265' && videoCodec != 'av1') {
          this.updateSetting('trailer_video_format', 'h265');
        }
      }
    }
    this.settingsService.updateSetting(key, value).subscribe((msg) => {
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

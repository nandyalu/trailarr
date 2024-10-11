import { NgIf } from '@angular/common';
import { Component } from '@angular/core';
import { TimeagoModule } from 'ngx-timeago';
import { ServerStats, Settings } from '../../models/settings';
import { SettingsService } from '../../services/settings.service';

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [TimeagoModule, NgIf],
  templateUrl: './about.component.html',
  styleUrl: './about.component.css'
})
export class AboutComponent {
  settings?: Settings;
  serverStats?: ServerStats;

  constructor(private settingsService: SettingsService) {}

  ngOnInit() {
    this.settingsService.getSettings().subscribe(settings => this.settings = settings);
    this.settingsService.getServerStats().subscribe(serverStats => this.serverStats = serverStats);
  }
}

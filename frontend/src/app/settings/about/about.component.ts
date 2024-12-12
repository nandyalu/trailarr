import { NgIf } from '@angular/common';
import { Component, ElementRef, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TimeagoModule } from 'ngx-timeago';
import { ServerStats, Settings } from '../../models/settings';
import { SettingsService } from '../../services/settings.service';

@Component({
    selector: 'app-about',
    imports: [TimeagoModule, NgIf, FormsModule],
    templateUrl: './about.component.html',
    styleUrl: './about.component.css'
})
export class AboutComponent {
  settings?: Settings;
  serverStats?: ServerStats;
  currentPassword = '';
  newPassword = '';
  updateError = '';
  updateSuccess = '';
  currentPasswordVisible = false;
  newPasswordVisible = false;


  constructor(private settingsService: SettingsService) {}

  ngOnInit() {
    this.settingsService.getSettings().subscribe(settings => this.settings = settings);
    this.settingsService.getServerStats().subscribe(serverStats => this.serverStats = serverStats);
  }

  updatePassword() {
    // this.settingsService.updatePassword().subscribe();
  }

  // Reference to the dialog element
  @ViewChild('passwordUpdateDialog') passwordUpdateDialog!: ElementRef<HTMLDialogElement>;

  clearPwUpdateFields(): void {
    this.currentPassword = '';
    this.newPassword = '';
    this.updateError = '';
    this.updateSuccess = '';
  }

  togglePasswordVisibility(input: HTMLInputElement): void {
    input.type = input.type === 'password' ? 'text' : 'password';
  }

  showPwUpdateDialog(): void {
    this.clearPwUpdateFields();
    this.passwordUpdateDialog.nativeElement.showModal(); // Open the dialog
  }

  closePwUpdateDialog(): void {
    this.clearPwUpdateFields();
    this.passwordUpdateDialog.nativeElement.close(); // Close the dialog
  }

  onConfirmUpdate() {
    console.log('Updating password');
    this.updateError = '';
    this.updateSuccess = '';
    this.settingsService.updatePassword(this.currentPassword, this.newPassword).subscribe((res: string) => {
      console.log(res);
      if (res.includes('Error')) {
        this.updateError = res;
      } else {
        this.updateSuccess = res;
        setTimeout(() => {
          this.closePwUpdateDialog();
        }, 3000);
      }
    });
  }
}
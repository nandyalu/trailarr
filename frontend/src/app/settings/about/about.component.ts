import {NgIf} from '@angular/common';
import {Component, ElementRef, inject, OnInit, ViewChild} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {TimeagoModule} from 'ngx-timeago';
import {ServerStats, Settings} from '../../models/settings';
import {SettingsService} from '../../services/settings.service';
import {WebsocketService} from '../../services/websocket.service';

@Component({
  selector: 'app-about',
  imports: [TimeagoModule, NgIf, FormsModule],
  templateUrl: './about.component.html',
  styleUrl: './about.component.scss',
})
export class AboutComponent implements OnInit {
  private readonly settingsService = inject(SettingsService);
  private readonly websocketService = inject(WebsocketService);

  settings?: Settings;
  serverStats?: ServerStats;
  currentPassword = '';
  newUsername = '';
  newPassword = '';
  updateError = '';
  updateSuccess = '';
  currentPasswordVisible = false;
  newPasswordVisible = false;

  ngOnInit() {
    this.settingsService.getSettings().subscribe((settings) => (this.settings = settings));
    this.settingsService.getServerStats().subscribe((serverStats) => (this.serverStats = serverStats));
  }

  updatePassword() {
    // this.settingsService.updatePassword().subscribe();
  }

  async copyToClipboard(textToCopy: string) {
    if (!navigator.clipboard) {
      // Fallback to the old execCommand() way (for wider browser coverage)
      const tempInput = document.createElement('input');
      tempInput.value = textToCopy;
      document.body.appendChild(tempInput);
      tempInput.select();
      document.execCommand('copy');
      document.body.removeChild(tempInput);
      this.websocketService.showToast('Copied to clipboard!');
    } else {
      try {
        await navigator.clipboard.writeText(textToCopy);
        this.websocketService.showToast('Copied to clipboard!');
      } catch (err) {
        this.websocketService.showToast('Error copying text to clipboard.', 'Error');
        console.error('Failed to copy: ', err);
      }
    }
    return;
  }

  // Reference to the dialog element
  @ViewChild('passwordUpdateDialog') passwordUpdateDialog!: ElementRef<HTMLDialogElement>;
  dialogOpen = false;

  clearPwUpdateFields(): void {
    this.currentPassword = '';
    this.newPassword = '';
    this.updateError = '';
    this.updateSuccess = '';
  }

  togglePasswordVisibility(input: HTMLInputElement): void {
    input.type = input.type === 'password' ? 'text' : 'password';
  }

  getSubmitButtonState(): boolean {
    if (!this.currentPassword) {
      return true; // Disable the button if current password is empty
    }
    let newLoginValid = false;
    if (this.newUsername.length > 0) {
      newLoginValid = true;
    }
    if (this.newPassword.length > 4) {
      newLoginValid = true;
    }
    return !newLoginValid; // Enable the button if new username or password is filled
  }

  showPwUpdateDialog(): void {
    this.clearPwUpdateFields();
    this.dialogOpen = true;
    this.passwordUpdateDialog.nativeElement.showModal(); // Open the dialog
  }

  closePwUpdateDialog(): void {
    this.clearPwUpdateFields();
    this.passwordUpdateDialog.nativeElement.close(); // Close the dialog
    this.dialogOpen = false;
  }

  onConfirmUpdate() {
    console.log('Updating password');
    this.updateError = '';
    this.updateSuccess = '';
    this.settingsService.updatePassword(this.currentPassword, this.newUsername, this.newPassword).subscribe((res: string) => {
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

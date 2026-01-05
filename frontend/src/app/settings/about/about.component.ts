import {AsyncPipe, NgTemplateOutlet} from '@angular/common';
import {ChangeDetectionStrategy, Component, ElementRef, inject, OnInit, signal, viewChild} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {CopyToClipboardDirective} from 'src/app/helpers/copy-to-clipboard.directive';
import {TimediffPipe} from 'src/app/helpers/timediff.pipe';
import {ServerStats} from 'src/app/models/serverstats';
import {SettingsService} from '../../services/settings.service';

@Component({
  selector: 'app-about',
  imports: [AsyncPipe, CopyToClipboardDirective, FormsModule, TimediffPipe, NgTemplateOutlet],
  templateUrl: './about.component.html',
  styleUrl: './about.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AboutComponent implements OnInit {
  private readonly settingsService = inject(SettingsService);

  protected readonly settingsSignal = this.settingsService.settingsResource.value;
  serverStats = signal<ServerStats>({
    movies_count: 0,
    movies_monitored: 0,
    series_count: 0,
    series_monitored: 0,
    trailers_detected: 0,
    trailers_downloaded: 0,
  });
  currentPassword = '';
  newUsername = '';
  newPassword = '';
  updateError = '';
  updateSuccess = '';
  currentPasswordVisible = false;
  newPasswordVisible = false;

  ngOnInit() {
    // this.settingsService.getSettings().subscribe((settings) => (this.settings = settings));
    this.settingsService.getServerStats().subscribe((serverStats) => this.serverStats.set(serverStats));
  }

  // Reference to the dialog element
  readonly passwordUpdateDialog = viewChild.required<ElementRef<HTMLDialogElement>>('passwordUpdateDialog');
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
    if (this.newUsername.length > 1) {
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
    this.passwordUpdateDialog().nativeElement.showModal(); // Open the dialog
  }

  closePwUpdateDialog(): void {
    this.clearPwUpdateFields();
    this.passwordUpdateDialog().nativeElement.close(); // Close the dialog
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

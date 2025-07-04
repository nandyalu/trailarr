import {Component, effect, ElementRef, inject, output, signal, viewChild} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {ProfileService} from 'src/app/services/profile.service';

@Component({
  selector: 'app-profile-select-dialog',
  imports: [FormsModule],
  templateUrl: './profile-select-dialog.component.html',
  styleUrl: './profile-select-dialog.component.scss',
})
export class ProfileSelectDialogComponent {
  protected readonly profileService = inject(ProfileService);
  protected readonly allProfiles = this.profileService.allProfiles.value;

  onSubmit = output<number>();
  onClosed = output<void>();

  selectedProfileID = signal(0);

  readonly profileSelectDialog = viewChild.required<ElementRef<HTMLDialogElement>>('profileSelectDialog');
  protected showDialog = () => this.profileSelectDialog().nativeElement.showModal();
  protected closeDialog = () => this.profileSelectDialog().nativeElement.close();

  constructor() {
    effect(() => {
      this.selectedProfileID.set(0);
    });
  }

  ngAfterViewInit() {
    this.showDialog();
  }

  onConfirm() {
    this.onSubmit.emit(this.selectedProfileID());
    this.closeDialog();
  }

  onCancel() {
    this.onClosed.emit();
    this.closeDialog();
  }
}

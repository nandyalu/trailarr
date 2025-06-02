import {CommonModule} from '@angular/common';
import {Component, inject, signal, ViewContainerRef} from '@angular/core';
import {Router, RouterLink} from '@angular/router';
import {AddCustomFilterDialogComponent} from 'src/app/media/add-filter-dialog/add-filter-dialog.component';
import {ProfileService} from 'src/app/services/profile.service';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {RouteAdd, RouteEdit, RouteProfiles, RouteSettings} from 'src/routing';

@Component({
  selector: 'app-show-profiles',
  imports: [CommonModule, LoadIndicatorComponent, RouterLink],
  templateUrl: './show-profiles.component.html',
  styleUrl: './show-profiles.component.scss',
})
export class ShowProfilesComponent {
  protected readonly profileService = inject(ProfileService);
  private readonly router = inject(Router);
  private viewContainerRef = inject(ViewContainerRef);

  protected readonly isLoading = signal(true);

  protected readonly RouteAdd = RouteAdd;
  protected readonly RouteProfiles = RouteProfiles;
  protected readonly RouteEdit = RouteEdit;
  protected readonly RouteSettings = RouteSettings;

  openFilterDialog(): void {
    // Open the dialog for adding or editing a custom filter
    const dialogRef = this.viewContainerRef.createComponent(AddCustomFilterDialogComponent);
    dialogRef.setInput('customFilter', null); // Set to null to Create a new one
    dialogRef.setInput('filterType', 'TRAILER');
    dialogRef.instance.dialogClosed.subscribe((emitValue: number) => {
      if (emitValue >= 0) {
        // Reload the filters and open profile edit page
        this.profileService.allProfiles.reload();
        this.router.navigate(['/settings/profiles/edit', emitValue]);
      }
      // Else, Filter dialog closed without submission, do nothing
      dialogRef.destroy(); // Destroy the dialog component after use
    });
  }
}

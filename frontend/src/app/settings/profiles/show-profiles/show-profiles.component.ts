import {ChangeDetectionStrategy, Component, inject, signal, ViewContainerRef} from '@angular/core';
import {Router, RouterLink} from '@angular/router';
import {EditFilterDialogComponent} from 'src/app/media/dialogs/edit-filter-dialog/edit-filter-dialog.component';
import {ProfileService} from 'src/app/services/profile.service';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {RouteAdd, RouteEdit, RouteProfiles, RouteSettings} from 'src/routing';

@Component({
  selector: 'app-show-profiles',
  imports: [EditFilterDialogComponent, LoadIndicatorComponent, RouterLink],
  templateUrl: './show-profiles.component.html',
  styleUrl: './show-profiles.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ShowProfilesComponent {
  protected readonly profileService = inject(ProfileService);
  private readonly router = inject(Router);

  protected readonly RouteAdd = RouteAdd;
  protected readonly RouteProfiles = RouteProfiles;
  protected readonly RouteEdit = RouteEdit;
  protected readonly RouteSettings = RouteSettings;

  /** `protected` `readonly` Signal to toggle the Add/Edit Filter Dialog */
  protected readonly editFilterDialogOpen = signal(false);

  protected openFilterDialog(): void {
    // Open the dialog for adding or editing a custom filter
    this.editFilterDialogOpen.set(true);
  }

  /**
   * Handles the closure of the edit filter dialog.
   * Closes the dialog, reloads the profiles, and routes to the created profile.
   * @protected
   * @returns {void}
   */
  protected onFilterDialogClosed(id: number): void {
    this.editFilterDialogOpen.set(false);
    if (id >= 0) {
      this.profileService.allProfiles.reload();
      this.router.navigate(['/settings/profiles', id]);
    }
  }
}

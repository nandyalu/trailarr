import {Component, computed, effect, ElementRef, inject, input, viewChild, ViewContainerRef} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Router} from '@angular/router';
import {AddCustomFilterDialogComponent} from 'src/app/media/add-filter-dialog/add-filter-dialog.component';
import {CustomFilterCreate} from 'src/app/models/customfilter';
import {ProfileService} from 'src/app/services/profile.service';
import {OptionsSettingComponent} from '../settings/options-setting/options-setting.component';
import {RangeSettingComponent} from '../settings/range-setting/range-setting.component';
import {TextSettingComponent} from '../settings/text-setting/text-setting.component';

@Component({
  selector: 'app-edit-profile',
  imports: [FormsModule, OptionsSettingComponent, TextSettingComponent, RangeSettingComponent],
  templateUrl: './edit-profile.component.html',
  styleUrl: './edit-profile.component.scss',
})
export class EditProfileComponent {
  private viewContainerRef = inject(ViewContainerRef);
  private readonly router = inject(Router);

  profileId = input(0, {
    transform: (value: any) => {
      const num = Number(value);
      return isNaN(num) ? 0 : num;
    },
  });
  profileService = inject(ProfileService);
  protected readonly profile = this.profileService.selectedProfile;
  protected readonly minLimitMax = computed(() => {
    let _profile = this.profile();
    if (_profile && _profile.max_duration) {
      return _profile.max_duration - 60;
    }
    return 540; // Default to 600 - 60 seconds (9 minutes)
  });
  protected readonly maxLimitMin = computed(() => {
    let _profile = this.profile();
    if (_profile && _profile.min_duration) {
      return _profile.min_duration + 60;
    }
    return 90; // Default to 30 + 60 seconds (11 minutes)
  });

  trueFalseOptions = ['true', 'false'];
  fileFormatOptions = ['mkv', 'mp4', 'webm'];
  audioFormatOptions = ['aac', 'ac3', 'eac3', 'flac', 'opus', 'copy'];
  videoFormatOptions = ['h264', 'h265', 'vp8', 'vp9', 'av1', 'copy'];
  videoResolutionOptions = ['360', '480', '720', '1080', '1440', '2160'];
  subtitleFormatOptions = ['srt', 'vtt'];

  isLoading: boolean = false;
  updateResults: string[] = [];
  profileName = '';
  videoResolution = 1080;
  subtitlesLanguage = 'en';
  fileName = '';
  excludeWords = '';
  minDuration = 30;
  maxDuration = 600;
  searchQuery = '';
  emptyCustomFilter = {
    id: null,
    filter_name: '',
    filter_type: 'TRAILER',
    filters: [],
  } as CustomFilterCreate;
  customFilter = computed(() => {
    let _profile = this.profile();
    if (_profile && _profile.customfilter) {
      return _profile.customfilter as unknown as CustomFilterCreate;
    }
    return this.emptyCustomFilter;
  });

  constructor() {
    effect(() => {
      let id = this.profileId();
      this.profileService.selectedProfileId.set(id);
      if (id <= 0) {
        this.openFilterDialog();
      } else {
      }
      // let profile = this.profileService.selectedProfile();
      // if (profile) {
      //   this.customFilter = profile.customfilter as unknown as CustomFilterCreate;
      // }
    });
  }

  openFilterDialog(): void {
    // Open the dialog for adding or editing a custom filter
    const dialogRef = this.viewContainerRef.createComponent(AddCustomFilterDialogComponent);
    dialogRef.setInput('customFilter', this.customFilter());
    dialogRef.setInput('filterType', 'TRAILER');
    dialogRef.instance.dialogClosed.subscribe((emitValue: number) => {
      if (emitValue !== -1) {
        // Reload the filters
        // this.loadCustomFilters();
        this.profileService.allProfiles.reload();
      }
      // Else, Filter dialog closed without submission, do nothing
      dialogRef.destroy(); // Destroy the dialog component after use
    });
  }

  private readonly deleteDialog = viewChild.required<ElementRef<HTMLDialogElement>>('deleteProfileDialog');

  protected closeDeleteDialog = () => this.deleteDialog().nativeElement.close();
  protected showDeleteDialog = () => this.deleteDialog().nativeElement.showModal();

  protected onConfirmDelete() {
    this.closeDeleteDialog();
    this.profileService.deleteProfile(this.profileId());
    this.router.navigate(['/settings/profiles']);
  }
}

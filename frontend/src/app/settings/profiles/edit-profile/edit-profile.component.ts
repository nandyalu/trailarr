import {
  ChangeDetectionStrategy,
  Component,
  computed,
  effect,
  ElementRef,
  inject,
  input,
  signal,
  viewChild,
  ViewContainerRef,
} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {Router} from '@angular/router';
import {TrailerProfileCreate} from 'generated-sources/openapi';
import {AddCustomFilterDialogComponent} from 'src/app/media/add-filter-dialog/add-filter-dialog.component';
import {CustomFilterCreate} from 'src/app/models/customfilter';
import {ProfileService} from 'src/app/services/profile.service';
import {LoadIndicatorComponent} from 'src/app/shared/load-indicator';
import {OptionsSettingComponent} from '../settings/options-setting/options-setting.component';
import {RangeSettingComponent} from '../settings/range-setting/range-setting.component';
import {TextSettingComponent} from '../settings/text-setting/text-setting.component';

@Component({
  selector: 'app-edit-profile',
  imports: [FormsModule, LoadIndicatorComponent, OptionsSettingComponent, RangeSettingComponent, TextSettingComponent],
  templateUrl: './edit-profile.component.html',
  styleUrl: './edit-profile.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditProfileComponent {
  protected profileService = inject(ProfileService);
  private readonly router = inject(Router);
  private readonly viewContainerRef = inject(ViewContainerRef);

  profileId = input(0, {
    transform: (value: any) => {
      const num = Number(value);
      return isNaN(num) ? 0 : num;
    },
  });
  protected readonly profile = this.profileService.selectedProfile;
  protected readonly newProfileName = signal<string>('');
  protected readonly profileJSON = signal<string>('{}');
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
  videoResolutionOptions = ['480', '720', '1080', '1440', '2160', '0']; // '0' for best
  subtitleFormatOptions = ['srt', 'vtt'];

  // Disabled options
  protected readonly fileFormatsDisabled = computed(() => {
    let _profile = this.profile();
    let disabled: string[] = [];
    if (!_profile) {
      return disabled;
    }
    // Based on video formats
    switch (_profile.video_format) {
      case 'copy':
        disabled.push('mp4');
        disabled.push('webm');
        break;
      case 'h264':
      case 'h265':
        disabled.push('webm');
        break;
      case 'vp8':
      case 'vp9':
        disabled.push('mp4');
        break;
    }
    // Based on audio formats
    switch (_profile.audio_format) {
      case 'copy':
        disabled.push('mp4');
        disabled.push('webm');
        break;
      case 'aac':
      case 'ac3':
      case 'eac3':
      case 'flac':
        disabled.push('webm');
        break;
    }
    return disabled;
  });
  protected readonly videoFormatsDisabled = computed(() => {
    let _profile = this.profile();
    let disabled: string[] = [];
    if (!_profile) {
      return disabled;
    }
    // Based on file formats
    switch (_profile.file_format) {
      case 'mp4':
        disabled.push('vp8');
        disabled.push('vp9');
        break;
      case 'webm':
        disabled.push('h264');
        disabled.push('h265');
        break;
    }
    return disabled;
  });

  protected readonly audioFormatsDisabled = computed(() => {
    let _profile = this.profile();
    let disabled: string[] = [];
    if (!_profile) {
      return disabled;
    }
    // Based on file formats
    switch (_profile.file_format) {
      case 'webm':
        disabled.push('aac');
        disabled.push('ac3');
        disabled.push('eac3');
        disabled.push('flac');
        break;
    }
    return disabled;
  });

  protected readonly invalidFormatsWarning = computed(() => {
    let _profile = this.profile();
    if (!_profile) {
      return []; // No profile, no warnings
    }
    let warnings: string[] = [];
    // Check for invalid file format based on video format
    switch (_profile.video_format) {
      case 'copy':
        if (_profile.file_format !== 'mkv') {
          warnings.push('Video format "copy" requires file format "mkv".');
        }
        break;
      case 'h264':
      case 'h265':
        if (_profile.file_format === 'webm') {
          warnings.push(`Video format "${_profile.video_format}" is not compatible with file format "webm".`);
        }
        break;
      case 'vp8':
      case 'vp9':
        if (_profile.file_format === 'mp4') {
          warnings.push(`Video format "${_profile.video_format}" is not compatible with file format "mp4".`);
        }
        break;
    }
    // Check for invalid file format based on audio format
    switch (_profile.audio_format) {
      case 'copy':
        if (_profile.file_format !== 'mkv') {
          warnings.push('Audio format "copy" requires file format "mkv".');
        }
        break;
      case 'aac':
      case 'ac3':
      case 'eac3':
      case 'flac':
        if (_profile.file_format === 'webm') {
          warnings.push(`Audio format "${_profile.audio_format}" is not compatible with file format "webm".`);
        }
        break;
    }
    return warnings;
  });

  isLoading: boolean = false;
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

  setProfileIDeffect = effect(() => {
    let id = this.profileId();
    if (this.profileService.allProfiles.isLoading()) {
      console.log('Profile data is still loading. Waiting for it to complete.');
      return; // Wait until the profile data is loaded
    }
    if (!this.profileService.profileExists(id)) {
      console.warn(`Profile with ID '${id}' does not exist. Redirecting to profiles list.`);
      this.router.navigate(['/settings/profiles']);
      return;
    }
    this.profileService.selectedProfileId.set(id);
    if (id <= 0) {
      this.openFilterDialog();
    }
  });

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
      setTimeout(() => {
        dialogRef.destroy(); // Destroy the dialog component after use
      }, 3000);
    });
  }

  private readonly deleteDialog = viewChild.required<ElementRef<HTMLDialogElement>>('deleteProfileDialog');
  private readonly copyProfileDialog = viewChild.required<ElementRef<HTMLDialogElement>>('copyProfileDialog');
  private readonly jsonEditDialog = viewChild.required<ElementRef<HTMLDialogElement>>('jsonEditDialog');

  protected closeDeleteDialog = () => this.deleteDialog().nativeElement.close();
  protected showDeleteDialog = () => this.deleteDialog().nativeElement.showModal();

  protected closeCopyProfileDialog = () => this.copyProfileDialog().nativeElement.close();
  protected showCopyProfileDialog = () => {
    let _name = this.profile()!.customfilter.filter_name + ' - Copy';
    this.newProfileName.set(_name);
    this.copyProfileDialog().nativeElement.showModal();
  };

  protected closeJsonEditDialog = () => this.jsonEditDialog().nativeElement.close();
  protected showJsonEditDialog = () => {
    this.profileJSON.set(JSON.stringify(this.profile(), null, 2));
    this.jsonEditDialog().nativeElement.showModal();
  };

  protected onConfirmCopy() {
    const newProfile = {
      ...this.profile(),
      id: null, // Reset ID for new profile
      customfilter: {
        ...this.customFilter(),
        filters: this.customFilter().filters.map((filter) => ({...filter, id: null})), // Deep copy filters
        filter_name: this.newProfileName(), // Use the new profile name
        id: null, // Reset ID for new custom filter
      },
    } as unknown as TrailerProfileCreate;
    console.log('Profile copied:', newProfile);
    this.profileService.createProfile(newProfile).subscribe((createdProfileId) => {
      if (createdProfileId) {
        this.closeCopyProfileDialog();
        this.router.navigate(['/settings/profiles', createdProfileId]);
      } else {
        console.error('Failed to create new profile. Please try again.');
      }
    });
  }

  protected onJsonEditSave() {
    try {
      const parsedProfile = JSON.parse(this.profileJSON());
      // Log the parsed profile for debugging
      console.log('Profile updated:', parsedProfile);
      this.profileService.updateProfile(parsedProfile).subscribe((success) => {
        if (success) {
          this.closeJsonEditDialog();
        }
        // Service will handle the success or error notification
      });
    } catch (error) {
      console.error('Invalid JSON format:', error);
      // Handle invalid JSON format error (e.g., show a notification)
    }
  }

  protected onConfirmDelete() {
    this.closeDeleteDialog();
    this.profileService.deleteProfile(this.profileId());
    this.router.navigate(['/settings/profiles']);
  }
}

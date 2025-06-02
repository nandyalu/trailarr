import {httpResource} from '@angular/common/http';
import {computed, inject, Injectable, signal} from '@angular/core';
import {TrailerProfileRead, TrailerProfilesService} from 'generated-sources/openapi';
import {environment} from 'src/environment';
import {WebsocketService} from './websocket.service';

@Injectable({
  providedIn: 'root',
})
export class ProfileService {
  private profilesUrl = environment.apiUrl + environment.trailerprofiles;
  private _service = inject(TrailerProfilesService);
  private websocketService = inject(WebsocketService);

  readonly allProfiles = httpResource<TrailerProfileRead[]>(this.profilesUrl, {defaultValue: []});

  /* Signal to track the selected profile ID */
  readonly selectedProfileId = signal(0);

  /* Signal to fetch the selected profile if it doesn't exist in allProfiles */
  private readonly fetchSelectedProfileResource = httpResource<TrailerProfileRead>(() => {
    if (this.selectedProfileId() <= 0) {
      return undefined;
    }
    const profileExists = this.allProfiles.value().findIndex((profile) => profile.id === this.selectedProfileId());
    if (profileExists !== -1) return undefined;
    return this.profilesUrl + this.selectedProfileId();
  });

  /* Computed property to get the selected profile */
  /* This will first check if the profile exists in allProfiles, and if not, it will fetch it */
  readonly selectedProfile = computed(() => {
    const selectedId = this.selectedProfileId();
    if (selectedId <= 0) {
      return undefined; // No/Invalid profile selected
    }

    // Check if the profile exists in allProfiles
    const profile = this.allProfiles.value().find((profile) => profile.id === selectedId);
    if (profile) {
      return profile; // Return the profile from the local list
    }

    // If not found, return the value from the fetchSelectedProfileResource
    return this.fetchSelectedProfileResource.value();
  });

  updateSetting(key: keyof TrailerProfileRead, value: any) {
    const selectedId = this.selectedProfileId();
    if (selectedId <= 0) {
      throw new Error('No profile selected');
    }

    this._service
      .updateTrailerProfileSettingApiV1TrailerprofilesTrailerprofileIdSettingPost({
        trailerprofile_id: selectedId,
        body: {
          key: key,
          value: value,
        },
      })
      .subscribe({
        next: (updatedProfile) => {
          // Update the local allProfiles signal with the updated profile
          this.allProfiles.update((profiles) => {
            const index = profiles.findIndex((profile) => profile.id === updatedProfile.id);
            if (index !== -1) {
              profiles[index] = updatedProfile;
              return [...profiles];
            }
            return [...profiles, updatedProfile];
          });
          const _key = key.charAt(0).toUpperCase() + key.replaceAll('_', ' ').slice(1);
          this.websocketService.showToast(`${_key} set to '${value}' successfully!`, 'success');
        },
        error: (error) => {
          // Log the server's error message
          let errorMessage = 'An unknown error occurred!';
          if (error.error instanceof ErrorEvent) {
            // client-side error
            errorMessage = `Error: ${error.error.message}`;
          } else {
            // server-side error
            errorMessage = `Error: ${error.status} ${error.error.detail}`;
          }
          console.error('Failed to update profile setting:', errorMessage);
          this.websocketService.showToast(errorMessage, 'error');
        },
      });
  }

  deleteProfile(id: number) {
    if (id <= 0) {
      throw new Error('Invalid profile ID');
    }
    this._service.deleteTrailerProfileApiV1TrailerprofilesTrailerprofileIdDelete({trailerprofile_id: id}).subscribe({
      next: () => {
        // Reset the selected profile ID and reload profiles
        this.selectedProfileId.set(0);
        this.allProfiles.reload();
        this.websocketService.showToast('Profile deleted successfully!', 'success');
      },
      error: (error) => {
        // Log the server's error message
        let errorMessage = 'An unknown error occurred!';
        if (error.error instanceof ErrorEvent) {
          // client-side error
          errorMessage = `Error: ${error.error.message}`;
        } else {
          // server-side error
          errorMessage = `Error: ${error.status} ${error.error.detail}`;
        }
        console.error('Failed to delete profile:', errorMessage);
        this.websocketService.showToast(errorMessage, 'error');
      },
    });
  }
}

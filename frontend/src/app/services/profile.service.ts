import {httpResource} from '@angular/common/http';
import {computed, inject, Injectable, signal} from '@angular/core';
import {TrailerProfileCreate, TrailerProfileRead, TrailerProfilesService} from 'generated-sources/openapi';
import {Observable, of} from 'rxjs';
import {catchError, map} from 'rxjs/operators';
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

  profileExists(id: number): boolean {
    let exists = this.allProfiles.value().some((profile) => profile.id === id);
    if (exists) return true; // Profile exists in the local list
    // Else, send a notification that profile does not exist
    this.websocketService.showToast(`Profile with ID '${id}' does not exist.`, 'error');
    return false;
  }

  createProfile(profile: TrailerProfileCreate): Observable<number | null> {
    if (!profile || !profile.customfilter.filter_name) {
      this.websocketService.showToast('Profile name is required', 'error');
      console.error('Profile creation failed: Name is required');
      return of(null); // Return null observable if name is invalid
    }
    return this._service.createTrailerProfileApiV1TrailerprofilesPost({body: profile}).pipe(
      map((createdProfile) => {
        // Reload the Profiles
        this.allProfiles.reload();
        this.selectedProfileId.set(createdProfile.id); // Set the newly created profile as selected
        this.websocketService.showToast(`Profile '${createdProfile.customfilter.filter_name}' created successfully!`, 'success');
        return createdProfile.id;
      }),
      catchError((error) => {
        // Log the server's error message
        let errorMessage = 'An unknown error occurred!';
        if (error.error instanceof ErrorEvent) {
          // client-side error
          errorMessage = `Error: ${error.error.message}`;
        } else {
          // server-side error
          errorMessage = `Error: ${error.status} ${error.error.detail}`;
        }
        console.error('Failed to create profile:', errorMessage);
        this.websocketService.showToast(errorMessage, 'error');
        return of(null);
      }),
    );
  }

  updateProfile(profile: TrailerProfileRead): Observable<boolean> {
    if (!profile || !profile.customfilter.filter_name) {
      this.websocketService.showToast('Profile name is required', 'error');
      console.error('Profile update failed: Name is required');
      return of(false); // Return false observable if name is invalid
    }
    return this._service
      .updateTrailerProfileApiV1TrailerprofilesTrailerprofileIdPut({
        trailerprofile_id: profile.id,
        body: profile,
      })
      .pipe(
        map((updatedProfile) => {
          // Reload Profiles
          this.allProfiles.reload();
          this.websocketService.showToast(`Profile '${updatedProfile.customfilter.filter_name}' updated successfully!`, 'success');
          return true;
        }),
        catchError((error) => {
          // Log the server's error message
          let errorMessage = 'An unknown error occurred!';
          if (error.error instanceof ErrorEvent) {
            // client-side error
            errorMessage = `Error: ${error.error.message}`;
          } else {
            // server-side error
            errorMessage = `Error: ${error.status} ${error.error.detail}`;
          }
          console.error('Failed to update profile:', errorMessage);
          this.websocketService.showToast(errorMessage, 'error');
          return of(false);
        }),
      );
  }

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

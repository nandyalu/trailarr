import {HttpClient, httpResource} from '@angular/common/http';
import {computed, inject, Injectable, signal} from '@angular/core';
import {Observable, of, throwError} from 'rxjs';
import {catchError, map, tap} from 'rxjs/operators';
import {TrailerProfileCreate, TrailerProfileRead} from '../models/trailerprofile';
import {environment} from 'src/environment';
import {WebsocketService} from './websocket.service';

@Injectable({
  providedIn: 'root',
})
export class ProfileService {
  private readonly http = inject(HttpClient);
  private profilesUrl = environment.apiUrl + environment.trailerprofiles;
  private websocketService = inject(WebsocketService);

  readonly allProfiles = httpResource<TrailerProfileRead[]>(() => this.profilesUrl, {defaultValue: []});

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
    return this.http.post<TrailerProfileRead>(this.profilesUrl, profile).pipe(
      map((createdProfile) => {
        this.allProfiles.reload();
        this.selectedProfileId.set(createdProfile.id);
        this.websocketService.showToast(`Profile '${createdProfile.customfilter.filter_name}' created successfully!`, 'success');
        return createdProfile.id;
      }),
      catchError((error) => {
        let errorMessage = 'An unknown error occurred!';
        if (error.error instanceof ErrorEvent) {
          errorMessage = `Error: ${error.error.message}`;
        } else {
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
    return this.http.put<TrailerProfileRead>(`${this.profilesUrl}${profile.id}`, profile).pipe(
      map((updatedProfile) => {
        this.allProfiles.reload();
        this.websocketService.showToast(`Profile '${updatedProfile.customfilter.filter_name}' updated successfully!`, 'success');
        return true;
      }),
      catchError((error) => {
        let errorMessage = 'An unknown error occurred!';
        if (error.error instanceof ErrorEvent) {
          errorMessage = `Error: ${error.error.message}`;
        } else {
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

    this.http.post<TrailerProfileRead>(`${this.profilesUrl}${selectedId}/setting`, {key, value}).subscribe({
      next: (updatedProfile) => {
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
        let errorMessage = 'An unknown error occurred!';
        if (error.error instanceof ErrorEvent) {
          errorMessage = `Error: ${error.error.message}`;
        } else {
          errorMessage = `Error: ${error.status} ${error.error.detail}`;
        }
        console.error('Failed to update profile setting:', errorMessage);
        this.websocketService.showToast(errorMessage, 'error');
      },
    });
  }

  deleteProfile(id: number): Observable<boolean> {
    if (id <= 0) {
      throw new Error('Invalid profile ID');
    }
    return this.http.delete<boolean>(`${this.profilesUrl}${id}`).pipe(
      tap(() => {
        this.selectedProfileId.set(0);
        this.allProfiles.reload();
        this.websocketService.showToast('Profile deleted successfully!', 'success');
      }),
      catchError((error) => {
        let errorMessage = 'An unknown error occurred!';
        if (error.error instanceof ErrorEvent) {
          errorMessage = `Error: ${error.error.message}`;
        } else {
          errorMessage = `Error: ${error.status} ${error.error.detail}`;
        }
        console.error('Failed to delete profile:', errorMessage);
        this.websocketService.showToast(errorMessage, 'error');
        return throwError(() => error);
      }),
    );
  }
}

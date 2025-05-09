import {httpResource} from '@angular/common/http';
import {computed, Injectable, signal} from '@angular/core';
import {TrailerProfileRead} from 'generated-sources/openapi';
import {environment} from 'src/environment';

@Injectable({
  providedIn: 'root',
})
export class ProfileService {
  // private httpClient = inject(HttpClient);
  private profilesUrl = environment.apiUrl + environment.trailerprofiles;

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
}

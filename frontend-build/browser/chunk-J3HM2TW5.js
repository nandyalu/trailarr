import {
  TrailerProfilesService
} from "./chunk-U5GO6X62.js";
import {
  WebsocketService
} from "./chunk-KIVIDEQ5.js";
import {
  Injectable,
  computed,
  environment,
  httpResource,
  inject,
  setClassMetadata,
  signal,
  ɵɵdefineInjectable
} from "./chunk-FAGZ4ZSE.js";

// src/app/services/profile.service.ts
var ProfileService = class _ProfileService {
  constructor() {
    this.profilesUrl = environment.apiUrl + environment.trailerprofiles;
    this._service = inject(TrailerProfilesService);
    this.websocketService = inject(WebsocketService);
    this.allProfiles = httpResource(this.profilesUrl, { defaultValue: [] });
    this.selectedProfileId = signal(0);
    this.fetchSelectedProfileResource = httpResource(() => {
      if (this.selectedProfileId() <= 0) {
        return void 0;
      }
      const profileExists = this.allProfiles.value().findIndex((profile) => profile.id === this.selectedProfileId());
      if (profileExists !== -1)
        return void 0;
      return this.profilesUrl + this.selectedProfileId();
    });
    this.selectedProfile = computed(() => {
      const selectedId = this.selectedProfileId();
      if (selectedId <= 0) {
        return void 0;
      }
      const profile = this.allProfiles.value().find((profile2) => profile2.id === selectedId);
      if (profile) {
        return profile;
      }
      return this.fetchSelectedProfileResource.value();
    });
  }
  updateSetting(key, value) {
    const selectedId = this.selectedProfileId();
    if (selectedId <= 0) {
      throw new Error("No profile selected");
    }
    this._service.updateTrailerProfileSettingApiV1TrailerprofilesTrailerprofileIdSettingPost({
      trailerprofile_id: selectedId,
      body: {
        key,
        value
      }
    }).subscribe({
      next: (updatedProfile) => {
        this.allProfiles.update((profiles) => {
          const index = profiles.findIndex((profile) => profile.id === updatedProfile.id);
          if (index !== -1) {
            profiles[index] = updatedProfile;
            return [...profiles];
          }
          return [...profiles, updatedProfile];
        });
        const _key = key.charAt(0).toUpperCase() + key.replaceAll("_", " ").slice(1);
        this.websocketService.showToast(`${_key} set to '${value}' successfully!`, "success");
      },
      error: (error) => {
        let errorMessage = "An unknown error occurred!";
        if (error.error instanceof ErrorEvent) {
          errorMessage = `Error: ${error.error.message}`;
        } else {
          errorMessage = `Error: ${error.status} ${error.error.detail}`;
        }
        console.error("Failed to update profile setting:", errorMessage);
        this.websocketService.showToast(errorMessage, "error");
      }
    });
  }
  deleteProfile(id) {
    if (id <= 0) {
      throw new Error("Invalid profile ID");
    }
    this._service.deleteTrailerProfileApiV1TrailerprofilesTrailerprofileIdDelete({ trailerprofile_id: id }).subscribe({
      next: () => {
        this.selectedProfileId.set(0);
        this.allProfiles.reload();
        this.websocketService.showToast("Profile deleted successfully!", "success");
      },
      error: (error) => {
        let errorMessage = "An unknown error occurred!";
        if (error.error instanceof ErrorEvent) {
          errorMessage = `Error: ${error.error.message}`;
        } else {
          errorMessage = `Error: ${error.status} ${error.error.detail}`;
        }
        console.error("Failed to delete profile:", errorMessage);
        this.websocketService.showToast(errorMessage, "error");
      }
    });
  }
  static {
    this.\u0275fac = function ProfileService_Factory(__ngFactoryType__) {
      return new (__ngFactoryType__ || _ProfileService)();
    };
  }
  static {
    this.\u0275prov = /* @__PURE__ */ \u0275\u0275defineInjectable({ token: _ProfileService, factory: _ProfileService.\u0275fac, providedIn: "root" });
  }
};
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(ProfileService, [{
    type: Injectable,
    args: [{
      providedIn: "root"
    }]
  }], null, null);
})();

export {
  ProfileService
};
//# sourceMappingURL=chunk-J3HM2TW5.js.map

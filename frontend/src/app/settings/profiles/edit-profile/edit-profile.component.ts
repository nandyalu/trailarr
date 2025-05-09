import {Component, effect, inject, input} from '@angular/core';
import {ProfileService} from 'src/app/services/profile.service';

@Component({
  selector: 'app-edit-profile',
  imports: [],
  templateUrl: './edit-profile.component.html',
  styleUrl: './edit-profile.component.scss',
})
export class EditProfileComponent {
  profileId = input(0, {transform: Number});
  profileService = inject(ProfileService);

  constructor() {
    effect(() => {
      let id = this.profileId();
      console.log('Profile ID:', id);
      this.profileService.selectedProfileId.set(id);
    });
  }
}

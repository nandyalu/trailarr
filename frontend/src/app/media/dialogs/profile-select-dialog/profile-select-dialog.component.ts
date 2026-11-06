import {ChangeDetectionStrategy, Component, computed, ElementRef, inject, input, linkedSignal, output, viewChild} from '@angular/core';
import {FormsModule} from '@angular/forms';
import {TrailerProfileRead} from 'src/app/models/trailerprofile';
import {ProfileService} from 'src/app/services/profile.service';

/** One option of the profile list, with the reason it comes last. */
export interface ProfileOption {
  profile: TrailerProfileRead;
  matches: boolean;
}

/**
 * Puts the profiles whose filters match the media item first, in the order
 * given, and the others after them, in their own order (#707).
 *
 * @param profiles - Every profile, in the order the profile list gives.
 * @param matchingIds - The ids of the profiles that match, best first.
 * Null when the caller does not know which profiles match: the list then
 * keeps its order, and no profile is marked.
 */
export function orderProfiles(profiles: readonly TrailerProfileRead[], matchingIds: readonly number[] | null): ProfileOption[] {
  if (matchingIds === null) {
    return profiles.map((profile) => ({profile, matches: true}));
  }
  const byId = new Map(profiles.map((profile) => [profile.id, profile]));
  const matching = matchingIds.map((id) => byId.get(id)).filter((profile): profile is TrailerProfileRead => profile !== undefined);
  const matchingSet = new Set(matching.map((profile) => profile.id));
  return [
    ...matching.map((profile) => ({profile, matches: true})),
    ...profiles.filter((profile) => !matchingSet.has(profile.id)).map((profile) => ({profile, matches: false})),
  ];
}

@Component({
  selector: 'app-profile-select-dialog',
  imports: [FormsModule],
  templateUrl: './profile-select-dialog.component.html',
  styleUrl: './profile-select-dialog.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProfileSelectDialogComponent {
  protected readonly profileService = inject(ProfileService);
  protected readonly allProfiles = this.profileService.allProfiles.value;

  /** The ids of the profiles whose filters match the media item, best
   * first. They come first, and the first is selected. Null keeps the
   * list as it is. */
  readonly matchingProfileIds = input<readonly number[] | null>(null);

  onSubmit = output<number>();
  onClosed = output<void>();

  protected readonly options = computed(() => orderProfiles(this.allProfiles(), this.matchingProfileIds()));

  /** The first option, until the user picks another one. */
  readonly selectedProfileID = linkedSignal(() => this.options()[0]?.profile.id ?? 0);

  readonly profileSelectDialog = viewChild.required<ElementRef<HTMLDialogElement>>('profileSelectDialog');
  protected showDialog = () => this.profileSelectDialog().nativeElement.showModal();
  protected closeDialog = () => this.profileSelectDialog().nativeElement.close();

  ngAfterViewInit() {
    this.showDialog();
  }

  onConfirm() {
    this.onSubmit.emit(this.selectedProfileID());
    this.closeDialog();
  }

  onCancel() {
    this.onClosed.emit();
    this.closeDialog();
  }
}

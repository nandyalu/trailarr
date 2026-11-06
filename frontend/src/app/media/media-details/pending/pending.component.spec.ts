/**
 * What the Download Profiles matrix says about the TMDB upgrade (#707).
 *
 * The matrix said that the Refresh Video Lists task would ask TMDB about an
 * unmonitored item. That task skips unmonitored items, so it never did, and
 * the sentence also stopped after "will".
 */
import {provideHttpClient} from '@angular/common/http';
import {provideHttpClientTesting} from '@angular/common/http/testing';
import {TestBed} from '@angular/core/testing';
import {provideRouter} from '@angular/router';
import {MediaPendingProfile, MediaPendingView} from 'src/app/models/pending';
import {MediaService} from 'src/app/services/media.service';
import {PendingComponent} from './pending.component';

function row(partial: Partial<MediaPendingProfile>): MediaPendingProfile {
  return {
    profile_id: 1,
    profile_name: 'TV Trailers',
    enabled: true,
    matches: true,
    satisfied: true,
    satisfied_by: 5,
    satisfied_via: 'own_download',
    pending: false,
    upgrade: false,
    upgrade_state: 'awaiting_tmdb',
    backing_off: false,
    attempt_count: 0,
    last_error: null,
    next_eligible_at: null,
    ...partial,
  };
}

function detailFor(view: Partial<MediaPendingView>, profile: MediaPendingProfile): string {
  TestBed.configureTestingModule({
    imports: [PendingComponent],
    providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
  });
  const service = TestBed.inject(MediaService);
  vi.spyOn(service.mediaPendingResource, 'value').mockReturnValue({
    media_id: 7,
    monitor: true,
    has_tmdb_id: true,
    tmdb_asked: true,
    profiles: [profile],
    ...view,
  });
  const component = TestBed.createComponent(PendingComponent).componentInstance;
  return (component as unknown as {stateDetail(p: MediaPendingProfile): string}).stateDetail(profile);
}

describe('PendingComponent upgrade text', () => {
  it('says that an unmonitored item is skipped, not that a task will ask TMDB', () => {
    const text = detailFor({monitor: false, tmdb_asked: false}, row({}));

    expect(text).toContain('This item is not monitored');
    expect(text).toContain('Turn on monitoring');
    expect(text).not.toContain('Refresh Video Lists');
  });

  it('says that the refresh task asks TMDB about a monitored item, in a whole sentence', () => {
    const text = detailFor({monitor: true, tmdb_asked: false}, row({}));

    expect(text).toContain('The Refresh Video Lists task asks about it');
    expect(text).not.toMatch(/will$/);
  });

  it('names the missing TMDB id first, monitored or not', () => {
    expect(detailFor({monitor: false, has_tmdb_id: false}, row({}))).toContain('this item has no TMDB id');
  });

  it('says that a replaced video is not one the profile can use', () => {
    const text = detailFor(
      {monitor: true},
      row({satisfied: false, satisfied_by: null, satisfied_via: null, pending: true, upgrade: true, upgrade_state: 'replace_not_tmdb'}),
    );

    expect(text).toContain('it is not a TMDB video that this profile can use');
  });
});

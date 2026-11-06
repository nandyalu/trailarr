/**
 * The order of the profile list for a manual search or download (#707).
 *
 * The dialog selected the first profile of the whole list, so a TV show
 * got Movie Trailers. The profiles whose filters match the item now come
 * first, and the others say that they do not match.
 */
import {TrailerProfileRead} from 'src/app/models/trailerprofile';
import {orderProfiles} from './profile-select-dialog.component';

function profile(id: number, name: string): TrailerProfileRead {
  return {id, customfilter: {id, filter_name: name, filters: []}} as unknown as TrailerProfileRead;
}

const MOVIES = profile(1, 'Movie Trailers');
const SERIES = profile(2, 'TV Trailers');
const FOURK = profile(3, '4K Trailers');

describe('orderProfiles', () => {
  it('puts the matching profiles first, in the order given, and marks the others', () => {
    const options = orderProfiles([MOVIES, SERIES, FOURK], [3, 2]);

    expect(options.map((o) => [o.profile.id, o.matches])).toEqual([
      [3, true],
      [2, true],
      [1, false],
    ]);
  });

  it('keeps the list and marks nothing while the matching profiles are not known', () => {
    const options = orderProfiles([MOVIES, SERIES], null);

    expect(options.map((o) => [o.profile.id, o.matches])).toEqual([
      [1, true],
      [2, true],
    ]);
  });

  it('marks every profile when none matches, and skips an id it does not know', () => {
    const options = orderProfiles([MOVIES, SERIES], [99]);

    expect(options.map((o) => [o.profile.id, o.matches])).toEqual([
      [1, false],
      [2, false],
    ]);
  });
});

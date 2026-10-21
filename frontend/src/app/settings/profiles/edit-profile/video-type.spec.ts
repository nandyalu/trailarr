import {describe, expect, it} from 'vitest';
import {nonTrailerPlexNote, searchNote} from './video-type';

describe('searchNote', () => {
  it('is empty for a trailer profile with the search on, the default', () => {
    expect(searchNote('trailer', true)).toBe('');
    expect(searchNote(undefined, undefined)).toBe('');
    expect(searchNote('', true)).toBe('');
  });

  it('says known videos only when the search is off, for any type', () => {
    expect(searchNote('trailer', false)).toContain('Search YouTube is off. Trailarr takes the Trailer');
    expect(searchNote('featurette', false)).toContain('takes the Featurette of a media item from its known videos only');
    expect(searchNote('featurette', false)).toContain('The search settings do not apply.');
  });

  it('warns when the search is on for a type other than Trailer', () => {
    const note = searchNote('behind_the_scenes', true);
    expect(note).toContain('Search YouTube is on for a Behind the Scenes profile.');
    expect(note).toContain('not checked against TMDB');
  });
});

describe('nonTrailerPlexNote', () => {
  it('is empty for a trailer profile', () => {
    expect(nonTrailerPlexNote('trailer')).toBe('');
    expect(nonTrailerPlexNote(null)).toBe('');
  });

  it('says the setting applies to trailer profiles only', () => {
    expect(nonTrailerPlexNote('teaser')).toBe(
      'Skip If Plex Has Trailer applies to trailer profiles only. A Teaser downloads even when Plex has a trailer.',
    );
  });
});

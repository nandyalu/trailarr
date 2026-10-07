import {describe, expect, it} from 'vitest';
import {nonTrailerPlexNote, nonTrailerSearchNote} from './video-type';

describe('nonTrailerSearchNote', () => {
  it('is empty for a trailer profile, with or without a stored type', () => {
    expect(nonTrailerSearchNote('trailer')).toBe('');
    expect(nonTrailerSearchNote(undefined)).toBe('');
    expect(nonTrailerSearchNote('')).toBe('');
  });

  it('names the type and says the search settings do not apply', () => {
    const note = nonTrailerSearchNote('featurette');
    expect(note).toBe(
      'This profile downloads a Featurette. Trailarr takes it from the videos that TMDB lists and does not fall back to a YouTube search. The search settings do not apply.',
    );
    expect(nonTrailerSearchNote('behind_the_scenes')).toContain('downloads a Behind the Scenes.');
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

import {describe, expect, it} from 'vitest';
import {DEFAULT_VIDEO_TYPE, isTrailerType, VIDEO_TYPE_OPTIONS, VIDEO_TYPES, videoTypeLabel} from './trailerprofile';

describe('video types', () => {
  it('offers the seven types, the trailer first', () => {
    expect(VIDEO_TYPES).toEqual(['trailer', 'teaser', 'clip', 'featurette', 'behind_the_scenes', 'bloopers', 'other']);
    expect(VIDEO_TYPES[0]).toBe(DEFAULT_VIDEO_TYPE);
    expect(VIDEO_TYPE_OPTIONS.map((o) => o.label)).toEqual(['Trailer', 'Teaser', 'Clip', 'Featurette', 'Behind the Scenes', 'Bloopers', 'Other']);
  });

  it('labels a type, and reads a missing or unknown type like the backend', () => {
    expect(videoTypeLabel('featurette')).toBe('Featurette');
    expect(videoTypeLabel('Behind_The_Scenes')).toBe('Behind the Scenes');
    expect(videoTypeLabel(undefined)).toBe('Trailer');
    expect(videoTypeLabel('')).toBe('Trailer');
    expect(videoTypeLabel('opening_credits')).toBe('Other');
  });

  it('knows the trailer type, the only one that searches YouTube', () => {
    expect(isTrailerType('trailer')).toBe(true);
    expect(isTrailerType(undefined)).toBe(true);
    expect(isTrailerType(null)).toBe(true);
    expect(isTrailerType(' Trailer ')).toBe(true);
    expect(isTrailerType('teaser')).toBe(false);
  });
});

import {describe, expect, it} from 'vitest';
import {Download} from 'src/app/models/media';
import {countUnknownVideos, unknownVideosNote} from './unknown-videos';

const download = (profile_id: number, youtube_id: string, file_exists = true) =>
  ({profile_id, youtube_id, file_exists}) as unknown as Download;

describe('countUnknownVideos', () => {
  const byMedia = () =>
    new Map<number, Download[]>([
      [1, [download(1, 'unknown0000'), download(1, 'abc123')]],
      [2, [download(1, ''), download(2, 'unknown0000'), download(1, 'unknown0000', false)]],
    ]).values();

  it('counts the active trailers of the profile, and the unknown ones among them', () => {
    // Another profile's file and a deleted file do not count.
    expect(countUnknownVideos(byMedia(), 1)).toEqual({total: 3, unknown: 2});
  });

  it('counts nothing without a profile id', () => {
    expect(countUnknownVideos(byMedia(), undefined)).toEqual({total: 0, unknown: 0});
  });
});

describe('unknownVideosNote', () => {
  it('says the impact before the setting is turned on', () => {
    expect(unknownVideosNote({total: 2400, unknown: 250})).toMatch(/^250 of 2[,.\s\u00a0]?400 trailers of this profile have/);
    expect(unknownVideosNote({total: 10, unknown: 1})).toContain('1 of 10 trailers of this profile has');
    expect(unknownVideosNote({total: 10, unknown: 0})).toContain('None of the 10 trailers');
    expect(unknownVideosNote({total: 0, unknown: 0})).toContain('no trailers on disk yet');
  });
});

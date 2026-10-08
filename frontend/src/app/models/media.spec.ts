/**
 * The media status (Phase 9): only a trailer makes an item 'downloaded'.
 * The files scan records extras (a featurette, a deleted scene) as
 * downloads too, so an item with an extra and no trailer is still
 * 'missing', and it stays off the Home page. The `has_downloads` and
 * `download_count` filters keep counting every type.
 */
import {describe, expect, it} from 'vitest';
import {computeMediaStatus, Download, hasActiveTrailer, isTrailerDownload, mapDownload} from './media';

function download(overrides: Partial<Download> = {}): Download {
  return {
    id: 1,
    media_id: 1,
    path: '/media/d1.mp4',
    file_name: 'd1.mp4',
    file_hash: '',
    size: 1000,
    resolution: 1080,
    file_format: 'mp4',
    video_format: 'h264',
    audio_format: 'aac',
    audio_language: 'eng',
    subtitle_format: null,
    subtitle_language: null,
    duration: 120,
    youtube_id: 'abc',
    youtube_channel: '',
    file_exists: true,
    profile_id: 1,
    video_type: 'trailer',
    added_at: new Date(),
    updated_at: new Date(),
    ...overrides,
  };
}

describe('computeMediaStatus', () => {
  it('is downloading while a download is in flight, whatever is on disk', () => {
    expect(computeMediaStatus(true, [download()], true)).toBe('downloading');
    expect(computeMediaStatus(false, [], true)).toBe('downloading');
  });

  it('is downloaded for an active trailer', () => {
    expect(computeMediaStatus(true, [download()])).toBe('downloaded');
    expect(computeMediaStatus(false, [download()])).toBe('downloaded');
  });

  it('is missing for a featurette-only item: an extra is not a trailer', () => {
    const featurette = [download({video_type: 'featurette', profile_id: 2})];
    expect(computeMediaStatus(false, featurette)).toBe('missing');
    expect(computeMediaStatus(true, featurette)).toBe('monitored');
  });

  it('is downloaded when a trailer sits next to extras', () => {
    const mixed = [download({id: 1, video_type: 'featurette'}), download({id: 2, video_type: 'behind_the_scenes'}), download({id: 3, video_type: 'trailer'})];
    expect(computeMediaStatus(false, mixed)).toBe('downloaded');
  });

  it('ignores a trailer whose file is gone', () => {
    expect(computeMediaStatus(false, [download({file_exists: false})])).toBe('missing');
    expect(computeMediaStatus(true, [download({file_exists: false})])).toBe('monitored');
  });

  it('reads a download with no type as a trailer', () => {
    expect(computeMediaStatus(false, [download({video_type: '' as string})])).toBe('downloaded');
    expect(computeMediaStatus(false, [download({video_type: undefined as unknown as string})])).toBe('downloaded');
  });

  it('is monitored or missing with no downloads', () => {
    expect(computeMediaStatus(true, [])).toBe('monitored');
    expect(computeMediaStatus(false, [])).toBe('missing');
  });
});

describe('isTrailerDownload and hasActiveTrailer', () => {
  it('reads the type like the backend: missing is a trailer, case and spaces do not matter', () => {
    expect(isTrailerDownload(download({video_type: 'trailer'}))).toBe(true);
    expect(isTrailerDownload(download({video_type: ' Trailer '}))).toBe(true);
    expect(isTrailerDownload(download({video_type: ''}))).toBe(true);
    expect(isTrailerDownload(download({video_type: 'teaser'}))).toBe(false);
    expect(isTrailerDownload(download({video_type: 'featurette'}))).toBe(false);
  });

  it('needs an active download of the trailer type', () => {
    expect(hasActiveTrailer([])).toBe(false);
    expect(hasActiveTrailer([download({video_type: 'featurette'})])).toBe(false);
    expect(hasActiveTrailer([download({file_exists: false})])).toBe(false);
    expect(hasActiveTrailer([download({video_type: 'featurette'}), download({id: 2})])).toBe(true);
  });

  it('mapDownload fills a missing type with trailer, so an old row counts', () => {
    const mapped = mapDownload({id: 1, media_id: 1, file_exists: 1, profile_id: 1, added_at: '', updated_at: ''});
    expect(mapped.video_type).toBe('trailer');
    expect(hasActiveTrailer([mapped])).toBe(true);
  });
});

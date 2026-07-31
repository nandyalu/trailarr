import {describe, expect, it} from 'vitest';
import {computeMediaStatus, Media} from 'src/app/models/media';
import {applySelectedFilter} from './apply-filters';

function makeMedia(
  id: number,
  downloads: {file_exists: boolean; profile_id: number}[],
  overrides: Partial<Media> = {},
): Media {
  return {
    id,
    title: `Media ${id}`,
    monitor: false,
    trailer_exists: false,
    status: 'missing',
    is_movie: true,
    downloads,
    ...overrides,
  } as unknown as Media;
}

describe('applySelectedFilter — unknown_profile', () => {
  const withUnknown = makeMedia(1, [{file_exists: true, profile_id: 0}]);
  const withAssigned = makeMedia(2, [{file_exists: true, profile_id: 5}]);
  const withDeletedUnknown = makeMedia(3, [{file_exists: false, profile_id: 0}]);
  const withoutDownloads = makeMedia(4, []);
  const all = [withUnknown, withAssigned, withDeletedUnknown, withoutDownloads];

  it('matches only media having an active download with no profile', () => {
    const result = applySelectedFilter(all, 'unknown_profile', []);
    expect(result).toEqual([withUnknown]);
  });

  it('ignores deleted downloads with profile_id 0', () => {
    const result = applySelectedFilter([withDeletedUnknown], 'unknown_profile', []);
    expect(result).toEqual([]);
  });

  it('does not affect the all filter', () => {
    expect(applySelectedFilter(all, 'all', [])).toEqual(all);
  });
});

describe('applySelectedFilter — downloads-driven built-ins (Phase 3)', () => {
  // Mirror flags deliberately contradict the download rows: any filter
  // still reading trailer_exists fails these expectations.
  const withDownload = makeMedia(1, [{file_exists: true, profile_id: 5}], {trailer_exists: false});
  const staleFlag = makeMedia(2, [], {trailer_exists: true, monitor: true});
  const deletedDownload = makeMedia(3, [{file_exists: false, profile_id: 5}]);
  const all = [withDownload, staleFlag, deletedDownload];

  it('downloaded matches only media with an active download', () => {
    expect(applySelectedFilter(all, 'downloaded', [])).toEqual([withDownload]);
  });

  it('missing matches media without an active download', () => {
    expect(applySelectedFilter(all, 'missing', [])).toEqual([staleFlag, deletedDownload]);
  });

  it('unmonitored excludes media with an active download', () => {
    expect(applySelectedFilter(all, 'unmonitored', [])).toEqual([deletedDownload]);
  });

  it('downloading reads the (overlay-derived) status string', () => {
    const inflight = makeMedia(4, [], {status: 'downloading'});
    expect(applySelectedFilter([...all, inflight], 'downloading', [])).toEqual([inflight]);
  });

  it('movies/series require an active download', () => {
    const series = makeMedia(5, [{file_exists: true, profile_id: 1}], {is_movie: false});
    expect(applySelectedFilter([...all, series], 'movies', [])).toEqual([withDownload]);
    expect(applySelectedFilter([...all, series], 'series', [])).toEqual([series]);
  });
});

describe('computeMediaStatus (Phase 3)', () => {
  const active = [{file_exists: true}] as Media['downloads'];
  const deleted = [{file_exists: false}] as Media['downloads'];

  it('any active download wins', () => {
    expect(computeMediaStatus(false, active)).toBe('downloaded');
    expect(computeMediaStatus(true, active)).toBe('downloaded');
  });

  it('monitor decides when nothing is downloaded', () => {
    expect(computeMediaStatus(true, [])).toBe('monitored');
    expect(computeMediaStatus(false, [])).toBe('missing');
    expect(computeMediaStatus(true, deleted)).toBe('monitored');
  });

  it('downloading overlay takes precedence over everything', () => {
    expect(computeMediaStatus(true, active, true)).toBe('downloading');
  });
});

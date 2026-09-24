import {describe, expect, it} from 'vitest';
import {computeMediaStatus, Media} from 'src/app/models/media';
import {CustomFilter} from 'src/app/models/customfilter';
import {applySelectedFilter, MOVIES_ONLY_FILTERS} from './apply-filters';

function makeMedia(
  id: number,
  downloads: {file_exists: boolean; profile_id: number}[],
  overrides: Partial<Media> = {},
): Media {
  return {
    id,
    title: `Media ${id}`,
    monitor: false,
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

// The header count divides by a type total whenever MOVIES_ONLY_FILTERS names
// the selected filter. A filter listed under the wrong type, or a new
// type-narrowing filter added to the switch and not to the map, shows a count
// over the wrong total — which no view test would notice.
describe('MOVIES_ONLY_FILTERS agrees with applySelectedFilter', () => {
  const movie = makeMedia(1, [{file_exists: true, profile_id: 1}], {is_movie: true});
  const show = makeMedia(2, [{file_exists: true, profile_id: 1}], {is_movie: false});
  const all = [movie, show];

  it.each(Object.keys(MOVIES_ONLY_FILTERS))('narrows %s to the type the map claims', (filterName) => {
    const expected = MOVIES_ONLY_FILTERS[filterName];
    const result = applySelectedFilter(all, filterName, []);
    expect(result.length).toBeGreaterThan(0);
    expect(result.every((media) => media.is_movie === expected)).toBe(true);
  });

  it('leaves untyped filters out of the map, so they divide by the whole library', () => {
    for (const filterName of ['all', 'downloaded', 'downloading', 'missing', 'monitored', 'unmonitored', 'unknown_profile']) {
      expect(MOVIES_ONLY_FILTERS[filterName]).toBeUndefined();
    }
  });
});

describe('applySelectedFilter — downloads-driven built-ins (Phase 3)', () => {
  // Only download rows decide downloaded-ness (the legacy mirror flag is
  // gone since v0.11.0).
  const withDownload = makeMedia(1, [{file_exists: true, profile_id: 5}]);
  const staleFlag = makeMedia(2, [], {monitor: true});
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

describe('applySelectedFilter — has_downloads virtual filter (v0.11.0)', () => {
  const withDownload = makeMedia(1, [{file_exists: true, profile_id: 5}]);
  const deletedOnly = makeMedia(2, [{file_exists: false, profile_id: 5}]);
  const noDownloads = makeMedia(3, []);
  const all = [withDownload, deletedOnly, noDownloads];

  const makeCustomFilter = (value: string): CustomFilter[] =>
    [
      {
        id: 9,
        filter_name: 'HasTrailer',
        filter_type: 'MOVIES',
        filters: [{id: 90, customfilter_id: 9, filter_by: 'has_downloads', filter_condition: 'EQUALS', filter_value: value}],
      },
    ] as unknown as CustomFilter[];

  it('has_downloads = true matches only media with an active download', () => {
    expect(applySelectedFilter(all, 'HasTrailer', makeCustomFilter('true'))).toEqual([withDownload]);
  });

  it('has_downloads = false matches media with no active download (deleted counts as none)', () => {
    expect(applySelectedFilter(all, 'HasTrailer', makeCustomFilter('false'))).toEqual([deletedOnly, noDownloads]);
  });
});

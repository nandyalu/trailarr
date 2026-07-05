import {describe, expect, it} from 'vitest';
import {Media} from 'src/app/models/media';
import {applySelectedFilter} from './apply-filters';

function makeMedia(id: number, downloads: {file_exists: boolean; profile_id: number}[]): Media {
  return {
    id,
    title: `Media ${id}`,
    monitor: false,
    trailer_exists: false,
    status: 'missing',
    is_movie: true,
    downloads,
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

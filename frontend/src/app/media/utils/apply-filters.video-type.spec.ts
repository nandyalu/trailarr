import {describe, expect, it} from 'vitest';
import {CustomFilter, FilterType, StringFilterCondition} from 'src/app/models/customfilter';
import {Download, Media} from 'src/app/models/media';
import {applySelectedFilter} from './apply-filters';

/**
 * The `download_video_type` virtual field (Phase 9): ANY semantics over the
 * active downloads, string conditions, and a download without a type is a
 * trailer. The shared parity fixture cannot carry a typed download until the
 * backend fixture builder reads `video_type`, so the cases live here.
 */

const download = (overrides: Partial<Download>): Download =>
  ({
    id: 1,
    media_id: 1,
    file_exists: true,
    profile_id: 1,
    resolution: 1080,
    video_type: 'trailer',
    added_at: new Date(),
    updated_at: new Date(),
    ...overrides,
  }) as unknown as Download;

const media = (downloads: Download[]): Media =>
  ({id: 1, title: 'Typed Movie', is_movie: true, monitor: true, status: 'missing', downloads, files: null}) as unknown as Media;

const filterFor = (condition: StringFilterCondition, value: string): CustomFilter =>
  ({
    id: 1,
    filter_type: FilterType.HOME,
    filter_name: 'types',
    filters: [{id: 1, customfilter_id: 1, filter_by: 'download_video_type', filter_condition: condition, filter_value: value}],
  }) as unknown as CustomFilter;

const matches = (item: Media, condition: StringFilterCondition, value: string) =>
  applySelectedFilter([item], 'types', [filterFor(condition, value)]).length === 1;

describe('download_video_type filter', () => {
  it('never matches a media with no downloads', () => {
    expect(matches(media([]), StringFilterCondition.EQUALS, 'featurette')).toBe(false);
    expect(matches(media([]), StringFilterCondition.NOT_EQUALS, 'featurette')).toBe(false);
  });

  it('matches when an active download has the type', () => {
    const item = media([download({video_type: 'featurette'})]);
    expect(matches(item, StringFilterCondition.EQUALS, 'featurette')).toBe(true);
    expect(matches(item, StringFilterCondition.EQUALS, 'trailer')).toBe(false);
  });

  it('matches ANY download, not every one', () => {
    const item = media([download({id: 1, video_type: 'trailer'}), download({id: 2, video_type: 'featurette'})]);
    expect(matches(item, StringFilterCondition.EQUALS, 'featurette')).toBe(true);
    expect(matches(item, StringFilterCondition.EQUALS, 'trailer')).toBe(true);
    expect(matches(item, StringFilterCondition.EQUALS, 'teaser')).toBe(false);
    // NOT_EQUALS is ANY too: one download that is not a featurette is enough.
    expect(matches(item, StringFilterCondition.NOT_EQUALS, 'featurette')).toBe(true);
  });

  it('ignores a download whose file is gone', () => {
    const item = media([download({video_type: 'featurette', file_exists: false})]);
    expect(matches(item, StringFilterCondition.EQUALS, 'featurette')).toBe(false);
  });

  it('treats a download without a type as a trailer', () => {
    const item = media([download({video_type: undefined as unknown as string})]);
    expect(matches(item, StringFilterCondition.EQUALS, 'trailer')).toBe(true);
    expect(matches(item, StringFilterCondition.EQUALS, 'featurette')).toBe(false);
    expect(matches(item, StringFilterCondition.IS_NOT_EMPTY, '')).toBe(true);
  });

  it('supports the other string conditions', () => {
    const item = media([download({video_type: 'behind_the_scenes'})]);
    expect(matches(item, StringFilterCondition.CONTAINS, 'scenes')).toBe(true);
    expect(matches(item, StringFilterCondition.STARTS_WITH, 'behind')).toBe(true);
    expect(matches(item, StringFilterCondition.NOT_CONTAINS, 'trailer')).toBe(true);
    expect(matches(item, StringFilterCondition.ENDS_WITH, 'trailer')).toBe(false);
  });
});

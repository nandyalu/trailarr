import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {describe, expect, it} from 'vitest';
import {CustomFilter, FilterType} from 'src/app/models/customfilter';
import {Media} from 'src/app/models/media';
import {applySelectedFilter} from './apply-filters';

/**
 * Filter-evaluation parity tests (Phase 6).
 *
 * This spec and the backend `tests/core/base/utils/test_filter_parity.py` run
 * the SAME fixture, so the two evaluators cannot drift apart silently. When
 * you add a case, add it to the JSON — never to only one side.
 */
const FIXTURE_PATH = resolve(__dirname, '../../../../../backend/tests/fixtures/filter-cases.json');
const fixture = JSON.parse(readFileSync(FIXTURE_PATH, 'utf-8'));

interface DownloadSpec {
  file_exists: boolean;
  profile_id: number;
  resolution: number;
  days_ago: number;
}

interface FilterCase {
  name: string;
  media: string;
  filter_by: string;
  filter_condition: string;
  filter_value: string;
  expected: boolean;
}

function daysAgo(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString();
}

function buildMedia(overrides: {downloads?: DownloadSpec[]; added_at_days_ago?: number}): Media {
  const downloads = (overrides.downloads ?? []).map((spec, i) => ({
    id: i + 1,
    media_id: 1,
    path: `/nonexistent/d${i}.mkv`,
    file_name: `d${i}.mkv`,
    size: 1000,
    resolution: spec.resolution ?? 1080,
    file_exists: spec.file_exists ?? true,
    profile_id: spec.profile_id ?? 1,
    added_at: daysAgo(spec.days_ago ?? 0),
    updated_at: daysAgo(spec.days_ago ?? 0),
  }));
  return {
    id: 1,
    title: 'Parity Movie',
    year: 2024,
    is_movie: true,
    monitor: true,
    arr_monitored: true,
    status: 'missing',
    added_at: daysAgo(overrides.added_at_days_ago ?? 1),
    updated_at: daysAgo(overrides.added_at_days_ago ?? 1),
    downloads,
    files: null,
  } as unknown as Media;
}

function buildCustomFilter(testCase: FilterCase): CustomFilter {
  return {
    id: 1,
    filter_type: FilterType.HOME,
    filter_name: 'parity',
    filters: [
      {
        id: 1,
        customfilter_id: 1,
        filter_by: testCase.filter_by,
        filter_condition: testCase.filter_condition,
        filter_value: testCase.filter_value,
      },
    ],
  } as unknown as CustomFilter;
}

describe('filter parity — shared fixture with the backend', () => {
  for (const testCase of fixture.cases as FilterCase[]) {
    it(testCase.name, () => {
      const media = buildMedia(fixture.media[testCase.media]);
      const result = applySelectedFilter([media], 'parity', [buildCustomFilter(testCase)]);
      expect(result.length === 1).toBe(testCase.expected);
    });
  }
});

import {describe, expect, it} from 'vitest';
import {CustomFilter, FilterType} from 'src/app/models/customfilter';
import {Download, Media} from 'src/app/models/media';
import {applySelectedFilter} from './apply-filters';
import {
  activeTrailers,
  ALL_FIELDS,
  buildTrailerBlock,
  EMPTY_VALUE,
  FieldContext,
  fieldOptionGroups,
  fieldsForView,
  headerLabel,
  MAX_TRAILERS_PER_CARD,
  MEDIA_FIELDS,
  mediaCellValue,
  mediaTagValue,
  profileName,
  resolveFields,
  TRAILER_FIELDS,
  trailerCellLines,
  TrailerFieldDef,
} from './media-fields';

/**
 * Registry tests (Phase 9, decision 11): every trailer value function with
 * zero, one and three active downloads plus a deleted one; the cap; the
 * profile-name fallbacks; and one check that the registry and
 * `applyDownloadFilter` select the same rows.
 */

function daysAgo(days: number): Date {
  const d = new Date('2026-10-01T12:00:00Z');
  d.setDate(d.getDate() - days);
  return d;
}

function makeDownload(id: number, overrides: Partial<Download> = {}): Download {
  return {
    id,
    media_id: 1,
    path: `/media/d${id}.mp4`,
    file_name: `d${id}.mp4`,
    file_hash: '',
    size: 45 * 1024 * 1024,
    resolution: 1080,
    file_format: 'mp4',
    video_format: 'h264',
    audio_format: 'aac',
    audio_language: 'eng',
    subtitle_format: 'srt',
    subtitle_language: 'eng',
    duration: 135,
    youtube_id: 'abc',
    youtube_channel: 'Studio',
    file_exists: true,
    profile_id: 1,
    video_type: 'trailer',
    added_at: daysAgo(id),
    updated_at: daysAgo(id),
    ...overrides,
  };
}

function makeMedia(downloads: Download[], overrides: Partial<Media> = {}): Media {
  return {
    id: 1,
    title: 'Inception',
    year: 2010,
    is_movie: true,
    monitor: true,
    arr_monitored: true,
    media_exists: true,
    status: 'downloaded',
    runtime: 148,
    language: 'English',
    studio: 'Legendary',
    season_count: 0,
    overview: 'A thief.',
    imdb_id: 'tt1375666',
    txdb_id: '27205',
    folder_path: '/movies/Inception (2010)',
    media_filename: 'Inception.mkv',
    plex_rating_key: null,
    plex_trailer: null,
    added_at: daysAgo(30),
    updated_at: daysAgo(2),
    downloaded_at: daysAgo(1),
    downloads,
    files: null,
    ...overrides,
  } as unknown as Media;
}

const context: FieldContext = {profileNames: new Map([[1, 'Movies 1080p'], [2, 'Movies 4K']])};

const trailerField = (key: string): TrailerFieldDef => TRAILER_FIELDS.find((f) => f.key === key)!;

/** The value lines of one trailer field for a media item. */
function lines(key: string, media: Media): string[] {
  return trailerCellLines(trailerField(key), buildTrailerBlock(media), context);
}

const none = makeMedia([]);
const one = makeMedia([makeDownload(1)]);
// Three active trailers plus one deleted. Ids give the order: id 1 is newest.
const three = makeMedia([
  makeDownload(3, {resolution: 720, video_format: 'vp9', audio_format: 'opus', audio_language: 'fra', subtitle_format: null, subtitle_language: null, file_format: 'webm', duration: 61, size: 10 * 1024 * 1024, profile_id: 2, video_type: 'teaser'}),
  makeDownload(1),
  makeDownload(2, {profile_id: 0, resolution: 2160, video_format: 'h265', audio_format: 'ac3', subtitle_language: null, duration: 3725, size: 2 * 1024 * 1024 * 1024}),
  makeDownload(4, {file_exists: false, resolution: 480, profile_id: 9}),
]);

describe('activeTrailers', () => {
  it('returns nothing without downloads', () => {
    expect(activeTrailers(none)).toEqual([]);
  });

  it('returns the one active download', () => {
    expect(activeTrailers(one).map((d) => d.id)).toEqual([1]);
  });

  it('drops the deleted download and orders newest first', () => {
    expect(activeTrailers(three).map((d) => d.id)).toEqual([1, 2, 3]);
  });

  it('selects the same rows as applyDownloadFilter (has_downloads)', () => {
    const filter = {
      id: 1,
      filter_type: FilterType.HOME,
      filter_name: 'active',
      filters: [{id: 1, customfilter_id: 1, filter_by: 'has_downloads', filter_condition: 'EQUALS', filter_value: 'true'}],
    } as unknown as CustomFilter;
    const onlyDeleted = makeMedia([makeDownload(5, {file_exists: false})], {id: 2});
    const all = [none, one, three, onlyDeleted];
    const byFilter = applySelectedFilter(all, 'active', [filter]).map((m) => m.id);
    const byRegistry = all.filter((m) => activeTrailers(m).length > 0).map((m) => m.id);
    expect(byRegistry).toEqual(byFilter);
    // And the count field reads the same row count the download_count filter reads.
    const countFilter = {
      ...filter,
      filter_name: 'count3',
      filters: [{id: 2, customfilter_id: 1, filter_by: 'download_count', filter_condition: 'EQUALS', filter_value: '3'}],
    } as unknown as CustomFilter;
    expect(applySelectedFilter(all, 'count3', [countFilter]).map((m) => m.id)).toEqual(
      all.filter((m) => lines('download_count', m)[0] === '3').map((m) => m.id),
    );
  });
});

describe('trailer value functions', () => {
  it.each([
    ['download_video_type', ['trailer']],
    ['download_resolution', ['1080p']],
    ['download_video_codec', ['h264']],
    ['download_audio_codec', ['aac']],
    ['download_audio_language', ['eng']],
    ['download_subtitles', ['srt (eng)']],
    ['download_container', ['mp4']],
    ['download_duration', ['2m 15s']],
    ['download_size', ['45 MB']],
    ['download_profile', ['Movies 1080p']],
    ['download_count', ['1']],
  ])('%s with one active download', (key, expected) => {
    expect(lines(key, one)).toEqual(expected);
  });

  it.each([
    ['download_video_type', ['trailer', 'trailer', 'teaser']],
    ['download_resolution', ['1080p', '2160p', '720p']],
    ['download_video_codec', ['h264', 'h265', 'vp9']],
    ['download_audio_codec', ['aac', 'ac3', 'opus']],
    ['download_audio_language', ['eng', 'eng', 'fra']],
    ['download_subtitles', ['srt (eng)', 'srt', EMPTY_VALUE]],
    ['download_container', ['mp4', 'mp4', 'webm']],
    ['download_duration', ['2m 15s', '1h 2m 5s', '1m 1s']],
    ['download_size', ['45 MB', '2 GB', '10 MB']],
    ['download_profile', ['Movies 1080p', 'Unknown', 'Movies 4K']],
    ['download_count', ['3']],
  ])('%s with three active downloads and one deleted', (key, expected) => {
    expect(lines(key, three)).toEqual(expected);
  });

  it.each(TRAILER_FIELDS.map((f) => f.key))('%s shows nothing without an active download', (key) => {
    expect(lines(key, none)).toEqual(key === 'download_count' ? ['0'] : []);
  });

  it('falls back to trailer when the backend sends no video_type', () => {
    const noType = makeMedia([makeDownload(1, {video_type: undefined as unknown as string})]);
    expect(lines('download_video_type', noType)).toEqual(['trailer']);
  });

  it('shows a dash for an empty value', () => {
    const bare = makeMedia([makeDownload(1, {resolution: 0, video_format: '', audio_format: '', audio_language: null, file_format: '', duration: 0, size: 0})]);
    for (const key of ['download_resolution', 'download_video_codec', 'download_audio_codec', 'download_audio_language', 'download_container', 'download_duration', 'download_size']) {
      expect(lines(key, bare)).toEqual([EMPTY_VALUE]);
    }
  });
});

describe('profileName', () => {
  it('returns the profile name', () => {
    expect(profileName(2, context)).toBe('Movies 4K');
  });

  it('returns Unknown for profile id 0', () => {
    expect(profileName(0, context)).toBe('Unknown');
  });

  it('returns Deleted [id] for a profile that is gone', () => {
    expect(profileName(7, context)).toBe('Deleted [7]');
  });
});

describe('the cap', () => {
  const six = makeMedia([1, 2, 3, 4, 5, 6].map((id) => makeDownload(id)).concat(makeDownload(7, {file_exists: false})));

  it('is three', () => {
    expect(MAX_TRAILERS_PER_CARD).toBe(3);
  });

  it('shows the three newest and counts the rest', () => {
    const block = buildTrailerBlock(six);
    expect(block.shown.map((d) => d.id)).toEqual([1, 2, 3]);
    expect(block.more).toBe(3);
    expect(block.count).toBe(6);
  });

  it('shows no more line at the cap', () => {
    expect(buildTrailerBlock(three).more).toBe(0);
  });

  it('limits every per-trailer field but not the count', () => {
    for (const field of TRAILER_FIELDS) {
      const result = lines(field.key, six);
      expect(result).toEqual(field.summary ? ['6'] : expect.any(Array));
      if (!field.summary) expect(result).toHaveLength(MAX_TRAILERS_PER_CARD);
    }
  });
});

describe('registry lookups', () => {
  it('has unique keys', () => {
    const keys = ALL_FIELDS.map((f) => f.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it('offers overview in the expanded view only', () => {
    expect(fieldsForView('expanded').map((f) => f.key)).toContain('overview');
    expect(fieldsForView('table').map((f) => f.key)).not.toContain('overview');
  });

  it('groups the dialog options under Media and Trailers', () => {
    const groups = fieldOptionGroups('table');
    expect(groups.map((g) => g.label)).toEqual(['Media', 'Trailers']);
    expect(groups[1].options.map((o) => o.label)).toContain('Resolution');
    expect(groups[1].options.map((o) => o.key)).toEqual(TRAILER_FIELDS.map((f) => f.key));
  });

  it('prefixes a trailer header with Trailer and leaves a media header alone', () => {
    expect(headerLabel(trailerField('download_resolution'))).toBe('Trailer Resolution');
    expect(headerLabel(trailerField('download_video_type'))).toBe('Trailer Type');
    expect(headerLabel(MEDIA_FIELDS[0])).toBe('Year');
  });

  it('keeps the saved order and ignores a key it does not know', () => {
    const resolved = resolveFields(['runtime', 'no_such_field', 'download_size', 'year'], 'table');
    expect(resolved.map((f) => f.key)).toEqual(['runtime', 'download_size', 'year']);
  });

  it('still loads the v0.13.x default keys', () => {
    expect(resolveFields(['overview', 'runtime', 'language'], 'expanded')).toHaveLength(3);
    expect(resolveFields(['year', 'status', 'runtime', 'language', 'added_at'], 'table')).toHaveLength(5);
  });
});

describe('media value functions', () => {
  const field = (key: string) => MEDIA_FIELDS.find((f) => f.key === key)!;

  it('formats a table cell', () => {
    expect(mediaCellValue(field('year'), one)).toBe('2010');
    expect(mediaCellValue(field('status'), one)).toBe('Downloaded');
    expect(mediaCellValue(field('runtime'), one)).toBe('2h 28m');
    expect(mediaCellValue(field('monitor'), one)).toBe('Yes');
    expect(mediaCellValue(field('season_count'), one)).toBeNull();
    expect(mediaCellValue(field('plex_trailer'), one)).toBeNull();
    // A date field is formatted by the template.
    expect(mediaCellValue(field('added_at'), one)).toBeNull();
  });

  it('formats an expanded tag with its prefix or wording', () => {
    expect(mediaTagValue(field('imdb_id'), one)).toBe('IMDB: tt1375666');
    expect(mediaTagValue(field('monitor'), one)).toBe('Monitored');
    expect(mediaTagValue(field('arr_monitored'), one)).toBe('Arr: Monitored');
    expect(mediaTagValue(field('media_exists'), one)).toBe('Media: Yes');
    expect(mediaTagValue(field('plex_trailer'), one)).toBe('Plex Trailer: No');
    expect(mediaTagValue(field('plex_rating_key'), one)).toBeNull();
    const show = makeMedia([], {is_movie: false, season_count: 3});
    expect(mediaTagValue(field('season_count'), show)).toBe('3 Seasons');
    expect(mediaCellValue(field('season_count'), show)).toBe('3');
  });
});

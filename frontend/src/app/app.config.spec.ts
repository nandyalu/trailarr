import {DATE_PIPE_DEFAULT_OPTIONS, DatePipe} from '@angular/common';
import {describe, expect, it} from 'vitest';
import {appConfig} from './app.config';
import {parseDate} from './models/media';

/**
 * Dates are stored and sent as UTC. The `date` pipe must therefore render
 * them in the VIEWER's timezone.
 *
 * Regression guard for issue #650: a global `timezone: 'UTC'` in
 * DATE_PIPE_DEFAULT_OPTIONS made every `| date` in the app print the UTC
 * clock time, so a trailer added at 9am in Melbourne (UTC+10) showed as
 * the previous evening.
 */
function datePipeOptions(): {dateFormat?: string; timezone?: string} {
  const provider = appConfig.providers.find(
    (p): p is {provide: unknown; useValue: {dateFormat?: string; timezone?: string}} =>
      typeof p === 'object' && p !== null && 'provide' in p && (p as {provide: unknown}).provide === DATE_PIPE_DEFAULT_OPTIONS,
  );
  return provider?.useValue ?? {};
}

describe('DATE_PIPE_DEFAULT_OPTIONS', () => {
  it('does not pin the date pipe to a fixed timezone', () => {
    expect(datePipeOptions().timezone).toBeUndefined();
  });

  it('keeps the medium format so dates show a time', () => {
    expect(datePipeOptions().dateFormat).toBe('medium');
  });

  it('renders a UTC instant in the local timezone', () => {
    // 04:33 UTC is 14:33 in UTC+10 and 23:33 the previous day in UTC-5:
    // whatever the runner's zone, the rendered hour must match the local
    // hour of that instant, never the UTC hour.
    const utcInstant = parseDate('2026-08-15 04:33:57.854992')!;
    const pipe = new DatePipe('en-US', undefined, datePipeOptions());

    const rendered = pipe.transform(utcInstant);
    const expected = new DatePipe('en-US').transform(utcInstant, 'medium');

    expect(rendered).toBe(expected);
    expect(rendered).toContain(String(utcInstant.getHours() % 12 || 12));
  });
});

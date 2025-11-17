import {take} from 'rxjs/operators';
import {TestScheduler} from 'rxjs/testing';
import {TimediffPipe} from './timediff.pipe';

describe('TimediffPipe', () => {
  it('create an instance', () => {
    const pipe = new TimediffPipe();
    expect(pipe).toBeTruthy();
  });

  describe('TimediffPipe', () => {
    let pipe: TimediffPipe;
    let testScheduler: TestScheduler;

    beforeEach(() => {
      pipe = new TimediffPipe();
      testScheduler = new TestScheduler((actual, expected) => {
        expect(actual).toEqual(expected);
      });
    });

    it('create an instance', () => {
      expect(pipe).toBeTruthy();
    });

    describe('transform', () => {
      it('should return observable with invalidReturn for null value', (done) => {
        const result = pipe.transform(null);
        result.pipe(take(1)).subscribe((value) => {
          expect(value).toBe('Invalid date');
          done();
        });
      });

      it('should return observable with invalidReturn for undefined value', (done) => {
        const result = pipe.transform(undefined);
        result.pipe(take(1)).subscribe((value) => {
          expect(value).toBe('Invalid date');
          done();
        });
      });

      it('should return observable with custom invalidReturn for null value', (done) => {
        const customInvalid = 'Custom invalid';
        const result = pipe.transform(null, customInvalid);
        result.pipe(take(1)).subscribe((value) => {
          expect(value).toBe(customInvalid);
          done();
        });
      });

      it('should return observable with time difference for valid date', (done) => {
        const pastDate = new Date(Date.now() - 5000); // 5 seconds ago
        const result = pipe.transform(pastDate);
        result.pipe(take(1)).subscribe((value) => {
          expect(value).toBe('5 seconds ago');
          done();
        });
      });
    });

    describe('getTimeDifferenceString', () => {
      beforeEach(() => {
        jasmine.clock().install();
        jasmine.clock().mockDate(new Date('2023-01-01T12:00:00Z'));
      });

      afterEach(() => {
        jasmine.clock().uninstall();
      });

      it('should return invalidReturn for null value', () => {
        const result = pipe['getTimeDifferenceString'](null);
        expect(result).toBe('Invalid date');
      });

      it('should return custom invalidReturn for null value', () => {
        const customInvalid = 'Custom invalid';
        const result = pipe['getTimeDifferenceString'](null, customInvalid);
        expect(result).toBe(customInvalid);
      });

      it('should return invalidReturn for invalid date string', () => {
        spyOn(console, 'log');
        const result = pipe['getTimeDifferenceString']('invalid-date');
        expect(result).toBe('Invalid date');
        expect(console.log).toHaveBeenCalledWith('Invalid date in TimediffPipe:', 'invalid-date');
      });

      it('should return seconds difference for recent dates', () => {
        const pastDate = new Date(Date.now() - 30000); // 30 seconds ago
        const result = pipe['getTimeDifferenceString'](pastDate);
        expect(result).toBe('30 seconds ago');
      });

      it('should return singular second for 1 second difference', () => {
        const pastDate = new Date(Date.now() - 1000); // 1 second ago
        const result = pipe['getTimeDifferenceString'](pastDate);
        expect(result).toBe('1 second ago');
      });

      it('should return minutes difference', () => {
        const pastDate = new Date(Date.now() - 5 * 60000); // 5 minutes ago
        const result = pipe['getTimeDifferenceString'](pastDate);
        expect(result).toBe('5 minutes ago');
      });

      it('should return singular minute for 1 minute difference', () => {
        const pastDate = new Date(Date.now() - 60000); // 1 minute ago
        const result = pipe['getTimeDifferenceString'](pastDate);
        expect(result).toBe('1 minute ago');
      });

      it('should return hours difference', () => {
        const pastDate = new Date(Date.now() - 3 * 3600000); // 3 hours ago
        const result = pipe['getTimeDifferenceString'](pastDate);
        expect(result).toBe('3 hours ago');
      });

      it('should return singular hour for 1 hour difference', () => {
        const pastDate = new Date(Date.now() - 3600000); // 1 hour ago
        const result = pipe['getTimeDifferenceString'](pastDate);
        expect(result).toBe('1 hour ago');
      });

      it('should return days difference', () => {
        const pastDate = new Date(Date.now() - 3 * 86400000); // 3 days ago
        const result = pipe['getTimeDifferenceString'](pastDate);
        expect(result).toBe('3 days ago');
      });

      it('should return singular day for 1 day difference', () => {
        const pastDate = new Date(Date.now() - 86400000); // 1 day ago
        const result = pipe['getTimeDifferenceString'](pastDate);
        expect(result).toBe('1 day ago');
      });

      it('should handle future dates with "from now" suffix', () => {
        const futureDate = new Date(Date.now() + 3600000); // 1 hour from now
        const result = pipe['getTimeDifferenceString'](futureDate);
        expect(result).toBe('1 hour from now');
      });

      it('should handle string date input', () => {
        const result = pipe['getTimeDifferenceString']('2023-01-01T11:55:00Z');
        expect(result).toBeTruthy();
      });

      it('should handle number timestamp input', () => {
        const timestamp = new Date('2023-01-01T11:55:00Z').getTime();
        const result = pipe['getTimeDifferenceString'](timestamp);
        expect(result).toBeTruthy();
      });

      it('should prioritize larger time units', () => {
        const pastDate = new Date(Date.now() - (1 * 86400000 + 1 * 3600000 + 29 * 60000 + 30 * 1000)); // 1 day, 1 hour, 29 minutes, 30 seconds ago
        const result = pipe['getTimeDifferenceString'](pastDate);
        expect(result).toBeTruthy();
      });
    });
  });
});

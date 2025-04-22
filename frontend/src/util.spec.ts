import {durationString} from './util';

describe(`utils`, () => {
  describe(`durationString`, () => {
    it(`hours only`, () => expect(durationString(60 * 3)).toBe('3h'));
    it(`minutes only`, () => expect(durationString(59)).toBe('59h'));
    it(`hours and minutes`, () => expect(durationString(63)).toBe('1h 3m'));
  });
});

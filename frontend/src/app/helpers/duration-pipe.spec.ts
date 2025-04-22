import {TestBed} from '@angular/core/testing';
import {MockBuilder} from 'ng-mocks';
import {DurationConvertPipe} from './duration-pipe';

describe(`DurationConvertPipe`, () => {
  let instance: DurationConvertPipe;

  beforeEach(() => MockBuilder().provide(DurationConvertPipe));

  beforeEach(() => {
    instance = TestBed.inject(DurationConvertPipe);
  });

  it(`creates instance`, () => expect(instance).toBeTruthy());

  it(`transforms`, () => expect(instance.transform(62)).toBe('1h 2m'));
});
